"""Read-only official source versus market probability divergence report."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Mapping

from polymarket_alpha_lab.team_paper_guard import json_ready_no_floats


__all__ = (
    "DIVERGENCE_STATUSES",
    "SourceOfficialVsMarketSignalDivergenceInput",
    "SourceOfficialVsMarketSignalDivergenceReport",
    "build_source_official_vs_market_signal_divergence_report",
    "source_official_vs_market_signal_divergence_report_digest",
    "source_official_vs_market_signal_divergence_report_to_payload",
    "validate_source_official_vs_market_signal_divergence_public_payload",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MAX_FRESH_SOURCE_AGE_HOURS = Decimal("72.000000")

DIVERGENCE_STATUSES = (
    "official_market_divergence",
    "aligned",
    "stale_source_watch",
)

REASON_CODE_SEQUENCE = (
    "official_market_gap_below_threshold",
    "official_market_gap_meets_threshold",
    "independent_source_supports_official_signal",
    "independent_source_does_not_support_official_signal",
    "source_freshness_within_phase1_window",
    "source_freshness_outside_phase1_window",
)

MANUAL_NEXT_STEPS = (
    "manual_review_official_market_gap",
    "refresh_independent_source_before_manual_review",
    "no_manual_action_required",
)

PAYLOAD_DECIMAL_FIELDS = (
    "official_signal_probability",
    "market_implied_probability",
    "independent_source_probability",
    "divergence_threshold_probability",
    "source_freshness_age_hours",
    "official_market_probability_gap",
    "independent_official_probability_gap",
    "independent_market_probability_gap",
)

PAYLOAD_SCHEMA = (
    "official_signal_probability",
    "market_implied_probability",
    "independent_source_probability",
    "divergence_threshold_probability",
    "source_freshness_age_hours",
    "official_market_probability_gap",
    "independent_official_probability_gap",
    "independent_market_probability_gap",
    "divergence_status",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
)

_INPUT_PROBABILITY_FIELDS = (
    "official_signal_probability",
    "market_implied_probability",
    "independent_source_probability",
    "divergence_threshold_probability",
)


class _SourceDivergencePublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _SourceDivergencePublicDataclass and issubclass(
                base,
                _SourceDivergencePublicDataclass,
            ):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class SourceOfficialVsMarketSignalDivergenceInput(
    _SourceDivergencePublicDataclass,
):
    official_signal_probability: Decimal
    market_implied_probability: Decimal
    independent_source_probability: Decimal
    divergence_threshold_probability: Decimal
    source_freshness_age_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            SourceOfficialVsMarketSignalDivergenceInput,
            "source divergence input",
        )
        for field_name in _INPUT_PROBABILITY_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_freshness_age_hours",
            _normalize_age(
                "source_freshness_age_hours",
                self.source_freshness_age_hours,
            ),
        )
        _require_true_bool("paper_only", self.paper_only)
        _require_true_bool("report_only", self.report_only)
        _require_true_bool("readonly", self.readonly)


@dataclass(frozen=True)
class SourceOfficialVsMarketSignalDivergenceReport(
    _SourceDivergencePublicDataclass,
):
    official_signal_probability: Decimal
    market_implied_probability: Decimal
    independent_source_probability: Decimal
    divergence_threshold_probability: Decimal
    source_freshness_age_hours: Decimal
    official_market_probability_gap: Decimal
    independent_official_probability_gap: Decimal
    independent_market_probability_gap: Decimal
    divergence_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            SourceOfficialVsMarketSignalDivergenceReport,
            "source divergence report",
        )
        for field_name in _INPUT_PROBABILITY_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_freshness_age_hours",
            _normalize_age(
                "source_freshness_age_hours",
                self.source_freshness_age_hours,
            ),
        )
        for field_name in (
            "official_market_probability_gap",
            "independent_official_probability_gap",
            "independent_market_probability_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_gap(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "divergence_status",
            _normalize_member(
                "divergence_status",
                self.divergence_status,
                DIVERGENCE_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "manual_next_step",
            _normalize_member(
                "manual_next_step",
                self.manual_next_step,
                MANUAL_NEXT_STEPS,
            ),
        )
        _require_true_bool("paper_only", self.paper_only)
        _require_true_bool("report_only", self.report_only)
        _require_true_bool("readonly", self.readonly)
        _validate_report(self)

    @property
    def public_payload(self) -> dict[str, object]:
        return source_official_vs_market_signal_divergence_report_to_payload(self)

    @property
    def payload_digest(self) -> str:
        return source_official_vs_market_signal_divergence_report_digest(self)


def build_source_official_vs_market_signal_divergence_report(
    source: SourceOfficialVsMarketSignalDivergenceInput,
) -> SourceOfficialVsMarketSignalDivergenceReport:
    if type(source) is not SourceOfficialVsMarketSignalDivergenceInput:
        raise ValueError(
            "source must be a SourceOfficialVsMarketSignalDivergenceInput",
        )
    (
        official_market_gap,
        independent_official_gap,
        independent_market_gap,
        status,
        reason_codes,
        manual_next_step,
    ) = _findings(source)

    return SourceOfficialVsMarketSignalDivergenceReport(
        official_signal_probability=source.official_signal_probability,
        market_implied_probability=source.market_implied_probability,
        independent_source_probability=source.independent_source_probability,
        divergence_threshold_probability=source.divergence_threshold_probability,
        source_freshness_age_hours=source.source_freshness_age_hours,
        official_market_probability_gap=official_market_gap,
        independent_official_probability_gap=independent_official_gap,
        independent_market_probability_gap=independent_market_gap,
        divergence_status=status,
        reason_codes=reason_codes,
        manual_next_step=manual_next_step,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def source_official_vs_market_signal_divergence_report_to_payload(
    report: SourceOfficialVsMarketSignalDivergenceReport,
) -> dict[str, object]:
    if type(report) is not SourceOfficialVsMarketSignalDivergenceReport:
        raise ValueError(
            "report must be a SourceOfficialVsMarketSignalDivergenceReport",
        )
    _validate_report(report)
    payload = json_ready_no_floats(
        {
            "official_signal_probability": report.official_signal_probability,
            "market_implied_probability": report.market_implied_probability,
            "independent_source_probability": report.independent_source_probability,
            "divergence_threshold_probability": (
                report.divergence_threshold_probability
            ),
            "source_freshness_age_hours": report.source_freshness_age_hours,
            "official_market_probability_gap": (
                report.official_market_probability_gap
            ),
            "independent_official_probability_gap": (
                report.independent_official_probability_gap
            ),
            "independent_market_probability_gap": (
                report.independent_market_probability_gap
            ),
            "divergence_status": report.divergence_status,
            "reason_codes": report.reason_codes,
            "manual_next_step": report.manual_next_step,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_source_official_vs_market_signal_divergence_public_payload(payload)
    return payload


def source_official_vs_market_signal_divergence_report_digest(
    report: SourceOfficialVsMarketSignalDivergenceReport,
) -> str:
    payload = source_official_vs_market_signal_divergence_report_to_payload(report)
    return _digest_payload(payload)


def validate_source_official_vs_market_signal_divergence_public_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload) != PAYLOAD_SCHEMA:
        raise ValueError("payload must match the canonical source divergence schema")

    for field_name in PAYLOAD_DECIMAL_FIELDS:
        if type(payload[field_name]) is not str:
            raise ValueError(f"{field_name} must be serialized as a string")

    source = SourceOfficialVsMarketSignalDivergenceInput(
        official_signal_probability=Decimal(payload["official_signal_probability"]),
        market_implied_probability=Decimal(payload["market_implied_probability"]),
        independent_source_probability=Decimal(
            payload["independent_source_probability"],
        ),
        divergence_threshold_probability=Decimal(
            payload["divergence_threshold_probability"],
        ),
        source_freshness_age_hours=Decimal(payload["source_freshness_age_hours"]),
    )
    expected = build_source_official_vs_market_signal_divergence_report(source)
    for field_name in (
        "official_market_probability_gap",
        "independent_official_probability_gap",
        "independent_market_probability_gap",
    ):
        if Decimal(payload[field_name]) != getattr(expected, field_name):
            raise ValueError(f"{field_name} must match source divergence fields")
    if payload["divergence_status"] != expected.divergence_status:
        raise ValueError("divergence_status must match source divergence fields")
    if _normalize_payload_reason_codes(payload["reason_codes"]) != expected.reason_codes:
        raise ValueError("reason_codes must match source divergence fields")
    if payload["manual_next_step"] != expected.manual_next_step:
        raise ValueError("manual_next_step must match source divergence fields")
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    return payload


def _findings(
    source: SourceOfficialVsMarketSignalDivergenceInput,
) -> tuple[Decimal, Decimal, Decimal, str, tuple[str, ...], str]:
    official_market_gap = _abs_decimal(
        source.official_signal_probability - source.market_implied_probability,
    )
    independent_official_gap = _abs_decimal(
        source.independent_source_probability - source.official_signal_probability,
    )
    independent_market_gap = _abs_decimal(
        source.independent_source_probability - source.market_implied_probability,
    )

    if official_market_gap < source.divergence_threshold_probability:
        return (
            official_market_gap,
            independent_official_gap,
            independent_market_gap,
            "aligned",
            ("official_market_gap_below_threshold",),
            "no_manual_action_required",
        )

    supports_official = independent_official_gap <= independent_market_gap
    fresh_source = source.source_freshness_age_hours <= MAX_FRESH_SOURCE_AGE_HOURS
    reason_codes = [
        "official_market_gap_meets_threshold",
        (
            "independent_source_supports_official_signal"
            if supports_official
            else "independent_source_does_not_support_official_signal"
        ),
        (
            "source_freshness_within_phase1_window"
            if fresh_source
            else "source_freshness_outside_phase1_window"
        ),
    ]
    if supports_official and fresh_source:
        status = "official_market_divergence"
        manual_next_step = "manual_review_official_market_gap"
    elif supports_official:
        status = "stale_source_watch"
        manual_next_step = "refresh_independent_source_before_manual_review"
    else:
        status = "aligned"
        manual_next_step = "no_manual_action_required"
    return (
        official_market_gap,
        independent_official_gap,
        independent_market_gap,
        status,
        tuple(reason_codes),
        manual_next_step,
    )


def _validate_report(report: SourceOfficialVsMarketSignalDivergenceReport) -> None:
    (
        official_market_gap,
        independent_official_gap,
        independent_market_gap,
        status,
        reason_codes,
        manual_next_step,
    ) = _findings(
        SourceOfficialVsMarketSignalDivergenceInput(
            official_signal_probability=report.official_signal_probability,
            market_implied_probability=report.market_implied_probability,
            independent_source_probability=report.independent_source_probability,
            divergence_threshold_probability=report.divergence_threshold_probability,
            source_freshness_age_hours=report.source_freshness_age_hours,
        ),
    )
    expected_values = {
        "official_market_probability_gap": official_market_gap,
        "independent_official_probability_gap": independent_official_gap,
        "independent_market_probability_gap": independent_market_gap,
        "divergence_status": status,
        "reason_codes": reason_codes,
        "manual_next_step": manual_next_step,
    }
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match source divergence fields")


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_age(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_gap(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _normalize_member(
    field_name: str,
    value: object,
    supported_values: tuple[str, ...],
) -> str:
    if type(value) is not str or value not in supported_values:
        raise ValueError(f"{field_name} must be supported")
    return value


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    return _normalize_reason_code_items(value)


def _normalize_payload_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is list:
        return _normalize_reason_code_items(tuple(value))
    if type(value) is tuple:
        return _normalize_reason_code_items(value)
    raise ValueError("reason_codes must be a list")


def _normalize_reason_code_items(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes contains unsupported reason code")
        if reason_code in seen:
            raise ValueError("reason_codes must not contain duplicates")
        seen.add(reason_code)
    sequenced = tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in seen
    )
    if reason_codes != sequenced:
        raise ValueError("reason_codes must use canonical sequence")
    return sequenced


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_true_bool(field_name: str, value: object) -> None:
    if type(value) is not bool or value is not True:
        raise ValueError(f"{field_name} must be True")


def _abs_decimal(value: Decimal) -> Decimal:
    if value < ZERO:
        return -value
    return value


def _digest_payload(payload: dict[str, object]) -> str:
    return sha256(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"),
    ).hexdigest()
