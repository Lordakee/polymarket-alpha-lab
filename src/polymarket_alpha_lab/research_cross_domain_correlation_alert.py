"""Pure report-only cross-domain correlation risk alert reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_CROSS_DOMAIN_CORRELATION_ALERT_CONFIG_VERSION = (
    "cross-domain-correlation-alert-v1"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_TWO = Decimal("2.000000")
_FOUR = Decimal("4.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_ALERT_STATUSES = frozenset(("pass", "watch", "block"))
_STATUS_RISK_RANK = {"pass": 0, "watch": 1, "block": 2}
_STATUS_SORT_RANK = {"block": 0, "watch": 1, "pass": 2}
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_DOMAIN_SEQUENCE = ("politics", "btc", "equity_index", "gold", "soccer", "basketball")
_DOMAIN_RANK = {domain: index for index, domain in enumerate(_DOMAIN_SEQUENCE)}
_REASON_CODE_SEQUENCE = (
    "cross_domain_correlation_pass",
    "cross_domain_correlation_watch",
    "cross_domain_correlation_block",
    "absolute_correlation_watch",
    "absolute_correlation_block",
    "co_move_intensity_watch",
    "co_move_intensity_block",
    "catalyst_overlap_watch",
    "catalyst_overlap_block",
    "lag_alignment_watch",
    "lag_alignment_block",
    "correlation_risk_score_watch",
    "correlation_risk_score_block",
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "raw",
    "".join(("candi", "date")),
    "".join(("mar", "ket")),
    "".join(("so", "urce")),
    "".join(("u", "rl")),
    "".join(("d", "sn")),
    "".join(("ta", "ble")),
    "".join(("to", "ken")),
    "".join(("b", "uy")),
    "".join(("se", "ll")),
    "".join(("pos", "ition")),
    "".join(("recom", "mend")),
    "".join(("li", "ve")),
    "".join(("au", "th")),
    "".join(("wal", "let")),
    "".join(("or", "der")),
    "".join(("muta", "tion")),
)


@dataclass(frozen=True)
class ResearchCrossDomainCorrelationAlertConfig:
    config_version: str = DEFAULT_RESEARCH_CROSS_DOMAIN_CORRELATION_ALERT_CONFIG_VERSION
    absolute_correlation_watch_threshold: Decimal = Decimal("0.600000")
    absolute_correlation_block_threshold: Decimal = Decimal("0.800000")
    co_move_intensity_watch_threshold: Decimal = Decimal("0.500000")
    co_move_intensity_block_threshold: Decimal = Decimal("0.700000")
    catalyst_overlap_watch_threshold: Decimal = Decimal("0.500000")
    catalyst_overlap_block_threshold: Decimal = Decimal("0.700000")
    lag_alignment_watch_threshold: Decimal = Decimal("0.500000")
    lag_alignment_block_threshold: Decimal = Decimal("0.800000")
    correlation_risk_score_watch_threshold: Decimal = Decimal("0.500000")
    correlation_risk_score_block_threshold: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCrossDomainCorrelationAlertConfig:
            raise TypeError(
                "ResearchCrossDomainCorrelationAlertConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCrossDomainCorrelationAlertConfig:
            raise ValueError(
                "config must be exactly ResearchCrossDomainCorrelationAlertConfig",
            )
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_CROSS_DOMAIN_CORRELATION_ALERT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "absolute_correlation_watch_threshold",
            "absolute_correlation_block_threshold",
            "co_move_intensity_watch_threshold",
            "co_move_intensity_block_threshold",
            "catalyst_overlap_watch_threshold",
            "catalyst_overlap_block_threshold",
            "lag_alignment_watch_threshold",
            "lag_alignment_block_threshold",
            "correlation_risk_score_watch_threshold",
            "correlation_risk_score_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_order(
            "absolute_correlation",
            self.absolute_correlation_watch_threshold,
            self.absolute_correlation_block_threshold,
        )
        _require_threshold_order(
            "co_move_intensity",
            self.co_move_intensity_watch_threshold,
            self.co_move_intensity_block_threshold,
        )
        _require_threshold_order(
            "catalyst_overlap",
            self.catalyst_overlap_watch_threshold,
            self.catalyst_overlap_block_threshold,
        )
        _require_threshold_order(
            "lag_alignment",
            self.lag_alignment_watch_threshold,
            self.lag_alignment_block_threshold,
        )
        _require_threshold_order(
            "correlation_risk_score",
            self.correlation_risk_score_watch_threshold,
            self.correlation_risk_score_block_threshold,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchCrossDomainCorrelationAlertObservation:
    left_domain: str
    right_domain: str
    observed_at: datetime
    signed_correlation: Decimal
    co_move_intensity: Decimal
    catalyst_overlap: Decimal
    lag_alignment: Decimal
    confidence: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCrossDomainCorrelationAlertObservation:
            raise TypeError(
                "ResearchCrossDomainCorrelationAlertObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCrossDomainCorrelationAlertObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchCrossDomainCorrelationAlertObservation",
            )
        _require_domain("left_domain", self.left_domain)
        _require_domain("right_domain", self.right_domain)
        if self.left_domain == self.right_domain:
            raise ValueError("domains must be distinct")
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "signed_correlation",
            _require_signed_ratio_decimal("signed_correlation", self.signed_correlation),
        )
        for field_name in (
            "co_move_intensity",
            "catalyst_overlap",
            "lag_alignment",
            "confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchCrossDomainCorrelationAlertRow:
    pair_key: str
    left_domain: str
    right_domain: str
    observed_at: datetime
    signed_correlation: Decimal
    absolute_correlation: Decimal
    co_move_intensity: Decimal
    catalyst_overlap: Decimal
    lag_alignment: Decimal
    confidence: Decimal
    correlation_risk_score: Decimal
    confidence_adjusted_risk_score: Decimal
    alert_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCrossDomainCorrelationAlertRow:
            raise TypeError(
                "ResearchCrossDomainCorrelationAlertRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCrossDomainCorrelationAlertRow:
            raise ValueError("row must be exactly ResearchCrossDomainCorrelationAlertRow")
        _require_public_string("pair_key", self.pair_key)
        _require_domain("left_domain", self.left_domain)
        _require_domain("right_domain", self.right_domain)
        if self.left_domain == self.right_domain:
            raise ValueError("row domains must be distinct")
        if self.pair_key != _pair_key(self.left_domain, self.right_domain):
            raise ValueError("pair_key must match row domains")
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "signed_correlation",
            _require_signed_ratio_decimal("signed_correlation", self.signed_correlation),
        )
        for field_name in (
            "absolute_correlation",
            "co_move_intensity",
            "catalyst_overlap",
            "lag_alignment",
            "confidence",
            "correlation_risk_score",
            "confidence_adjusted_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_alert_status("alert_status", self.alert_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchCrossDomainCorrelationAlertReport:
    generated_at: datetime
    config_version: str
    alert_status: str
    observed_pair_count: Decimal
    covered_domain_count: Decimal
    pass_pair_count: Decimal
    watch_pair_count: Decimal
    block_pair_count: Decimal
    average_correlation_risk_score: Decimal
    max_correlation_risk_score: Decimal
    rows: tuple[ResearchCrossDomainCorrelationAlertRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCrossDomainCorrelationAlertReport:
            raise TypeError(
                "ResearchCrossDomainCorrelationAlertReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCrossDomainCorrelationAlertReport:
            raise ValueError(
                "report must be exactly ResearchCrossDomainCorrelationAlertReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_CROSS_DOMAIN_CORRELATION_ALERT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_alert_status("alert_status", self.alert_status)
        for field_name in (
            "observed_pair_count",
            "covered_domain_count",
            "pass_pair_count",
            "watch_pair_count",
            "block_pair_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_correlation_risk_score",
            "max_correlation_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchCrossDomainCorrelationAlertReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_cross_domain_correlation_alert_report(
    observations: Sequence[ResearchCrossDomainCorrelationAlertObservation],
    *,
    generated_at: datetime,
    config: ResearchCrossDomainCorrelationAlertConfig | None = None,
) -> ResearchCrossDomainCorrelationAlertReport:
    if config is None:
        config = ResearchCrossDomainCorrelationAlertConfig()
    if type(config) is not ResearchCrossDomainCorrelationAlertConfig:
        raise ValueError("config must be a ResearchCrossDomainCorrelationAlertConfig")
    generated_at = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    normalized_observations = _normalize_observations(observations)
    for observation in normalized_observations:
        if observation.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    rows = _build_rows(normalized_observations, config)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "alert_status": _report_status(rows),
        "observed_pair_count": _decimal_count(len(rows)),
        "covered_domain_count": _decimal_count(len(_covered_domains(rows))),
        "pass_pair_count": _decimal_count(_status_count(rows, "pass")),
        "watch_pair_count": _decimal_count(_status_count(rows, "watch")),
        "block_pair_count": _decimal_count(_status_count(rows, "block")),
        "average_correlation_risk_score": _average(
            tuple(row.correlation_risk_score for row in rows),
        ),
        "max_correlation_risk_score": max(
            (row.correlation_risk_score for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchCrossDomainCorrelationAlertReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_cross_domain_correlation_alert_payload(
    report: ResearchCrossDomainCorrelationAlertReport,
) -> dict[str, object]:
    if type(report) is not ResearchCrossDomainCorrelationAlertReport:
        raise ValueError("report must be a ResearchCrossDomainCorrelationAlertReport")
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    return report.payload


def _build_rows(
    observations: tuple[ResearchCrossDomainCorrelationAlertObservation, ...],
    config: ResearchCrossDomainCorrelationAlertConfig,
) -> tuple[ResearchCrossDomainCorrelationAlertRow, ...]:
    return _rank_rows(tuple(_row_for_observation(observation, config) for observation in observations))


def _row_for_observation(
    observation: ResearchCrossDomainCorrelationAlertObservation,
    config: ResearchCrossDomainCorrelationAlertConfig,
) -> ResearchCrossDomainCorrelationAlertRow:
    absolute_correlation = _quantize(abs(observation.signed_correlation))
    correlation_risk_score = _average(
        (
            absolute_correlation,
            observation.co_move_intensity,
            observation.catalyst_overlap,
            observation.lag_alignment,
        ),
    )
    confidence_adjusted_risk_score = _clamp_ratio(
        correlation_risk_score * observation.confidence,
    )
    alert_status = _row_status(
        config,
        absolute_correlation=absolute_correlation,
        co_move_intensity=observation.co_move_intensity,
        catalyst_overlap=observation.catalyst_overlap,
        lag_alignment=observation.lag_alignment,
        correlation_risk_score=correlation_risk_score,
    )
    return ResearchCrossDomainCorrelationAlertRow(
        pair_key=_pair_key(observation.left_domain, observation.right_domain),
        left_domain=observation.left_domain,
        right_domain=observation.right_domain,
        observed_at=observation.observed_at,
        signed_correlation=observation.signed_correlation,
        absolute_correlation=absolute_correlation,
        co_move_intensity=observation.co_move_intensity,
        catalyst_overlap=observation.catalyst_overlap,
        lag_alignment=observation.lag_alignment,
        confidence=observation.confidence,
        correlation_risk_score=correlation_risk_score,
        confidence_adjusted_risk_score=confidence_adjusted_risk_score,
        alert_status=alert_status,
        reason_codes=_row_reason_codes(
            config,
            alert_status=alert_status,
            absolute_correlation=absolute_correlation,
            co_move_intensity=observation.co_move_intensity,
            catalyst_overlap=observation.catalyst_overlap,
            lag_alignment=observation.lag_alignment,
            correlation_risk_score=correlation_risk_score,
        ),
    )


def _row_status(
    config: ResearchCrossDomainCorrelationAlertConfig,
    *,
    absolute_correlation: Decimal,
    co_move_intensity: Decimal,
    catalyst_overlap: Decimal,
    lag_alignment: Decimal,
    correlation_risk_score: Decimal,
) -> str:
    if (
        absolute_correlation >= config.absolute_correlation_block_threshold
        or co_move_intensity >= config.co_move_intensity_block_threshold
        or catalyst_overlap >= config.catalyst_overlap_block_threshold
        or lag_alignment >= config.lag_alignment_block_threshold
        or correlation_risk_score >= config.correlation_risk_score_block_threshold
    ):
        return "block"
    if (
        absolute_correlation >= config.absolute_correlation_watch_threshold
        or co_move_intensity >= config.co_move_intensity_watch_threshold
        or catalyst_overlap >= config.catalyst_overlap_watch_threshold
        or lag_alignment >= config.lag_alignment_watch_threshold
        or correlation_risk_score >= config.correlation_risk_score_watch_threshold
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    config: ResearchCrossDomainCorrelationAlertConfig,
    *,
    alert_status: str,
    absolute_correlation: Decimal,
    co_move_intensity: Decimal,
    catalyst_overlap: Decimal,
    lag_alignment: Decimal,
    correlation_risk_score: Decimal,
) -> tuple[str, ...]:
    reason_codes = [f"cross_domain_correlation_{alert_status}"]
    _append_threshold_reason(
        reason_codes,
        "absolute_correlation",
        absolute_correlation,
        config.absolute_correlation_watch_threshold,
        config.absolute_correlation_block_threshold,
    )
    _append_threshold_reason(
        reason_codes,
        "co_move_intensity",
        co_move_intensity,
        config.co_move_intensity_watch_threshold,
        config.co_move_intensity_block_threshold,
    )
    _append_threshold_reason(
        reason_codes,
        "catalyst_overlap",
        catalyst_overlap,
        config.catalyst_overlap_watch_threshold,
        config.catalyst_overlap_block_threshold,
    )
    _append_threshold_reason(
        reason_codes,
        "lag_alignment",
        lag_alignment,
        config.lag_alignment_watch_threshold,
        config.lag_alignment_block_threshold,
    )
    _append_threshold_reason(
        reason_codes,
        "correlation_risk_score",
        correlation_risk_score,
        config.correlation_risk_score_watch_threshold,
        config.correlation_risk_score_block_threshold,
    )
    return _normalize_reason_codes(tuple(reason_codes))


def _append_threshold_reason(
    reason_codes: list[str],
    label: str,
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if value >= block_threshold:
        reason_codes.append(f"{label}_block")
    elif value >= watch_threshold:
        reason_codes.append(f"{label}_watch")


def _normalize_observations(
    observations: Sequence[ResearchCrossDomainCorrelationAlertObservation],
) -> tuple[ResearchCrossDomainCorrelationAlertObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchCrossDomainCorrelationAlertObservation] = []
    seen: set[str] = set()
    for observation in observations:
        if type(observation) is not ResearchCrossDomainCorrelationAlertObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchCrossDomainCorrelationAlertObservation",
            )
        _require_hard_flags("observation", observation)
        pair_key = _pair_key(observation.left_domain, observation.right_domain)
        if pair_key in seen:
            raise ValueError("domain pairs must be unique")
        seen.add(pair_key)
        normalized.append(observation)
    return tuple(sorted(normalized, key=lambda item: _pair_key(item.left_domain, item.right_domain)))


def _normalize_rows(rows: object) -> tuple[ResearchCrossDomainCorrelationAlertRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized: list[ResearchCrossDomainCorrelationAlertRow] = []
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchCrossDomainCorrelationAlertRow:
            raise ValueError("rows must contain ResearchCrossDomainCorrelationAlertRow")
        if row.pair_key in seen:
            raise ValueError("row pair_key must be unique")
        seen.add(row.pair_key)
        normalized.append(row)
    ranked_rows = _rank_rows(tuple(normalized))
    if ranked_rows != rows:
        raise ValueError("rows must be sorted by alert risk")
    return ranked_rows


def _rank_rows(
    rows: tuple[ResearchCrossDomainCorrelationAlertRow, ...],
) -> tuple[ResearchCrossDomainCorrelationAlertRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _STATUS_SORT_RANK[row.alert_status],
                -row.correlation_risk_score,
                row.pair_key,
            ),
        ),
    )


def _covered_domains(rows: tuple[ResearchCrossDomainCorrelationAlertRow, ...]) -> tuple[str, ...]:
    domains = {row.left_domain for row in rows}
    domains.update(row.right_domain for row in rows)
    return tuple(sorted(domains, key=lambda domain: _DOMAIN_RANK[domain]))


def _status_count(rows: tuple[ResearchCrossDomainCorrelationAlertRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.alert_status == status)


def _report_status(rows: tuple[ResearchCrossDomainCorrelationAlertRow, ...]) -> str:
    if not rows:
        return "pass"
    return max((row.alert_status for row in rows), key=lambda status: _STATUS_RISK_RANK[status])


def _report_reason_codes(
    rows: tuple[ResearchCrossDomainCorrelationAlertRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("cross_domain_correlation_pass",)
    status_reason = f"cross_domain_correlation_{_report_status(rows)}"
    risk_reasons: set[str] = set()
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code in (
                "cross_domain_correlation_pass",
                "cross_domain_correlation_watch",
                "cross_domain_correlation_block",
            ):
                continue
            risk_reasons.add(reason_code)
    return _normalize_reason_codes(
        (
            status_reason,
            *(
                reason_code
                for reason_code in _REASON_CODE_SEQUENCE
                if reason_code in risk_reasons
            ),
        ),
    )


def _validate_row_consistency(row: ResearchCrossDomainCorrelationAlertRow) -> None:
    if row.absolute_correlation != _quantize(abs(row.signed_correlation)):
        raise ValueError("absolute_correlation must match signed_correlation")
    expected_risk_score = _average(
        (
            row.absolute_correlation,
            row.co_move_intensity,
            row.catalyst_overlap,
            row.lag_alignment,
        ),
    )
    if row.correlation_risk_score != expected_risk_score:
        raise ValueError("correlation_risk_score must match row metrics")
    if row.confidence_adjusted_risk_score != _clamp_ratio(
        row.correlation_risk_score * row.confidence,
    ):
        raise ValueError("confidence_adjusted_risk_score must match row metrics")


def _validate_report_consistency(report: ResearchCrossDomainCorrelationAlertReport) -> None:
    if report.observed_pair_count != _decimal_count(len(report.rows)):
        raise ValueError("observed_pair_count must match rows")
    if report.covered_domain_count != _decimal_count(len(_covered_domains(report.rows))):
        raise ValueError("covered_domain_count must match rows")
    if report.pass_pair_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_pair_count must match rows")
    if report.watch_pair_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_pair_count must match rows")
    if report.block_pair_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_pair_count must match rows")
    if report.alert_status != _report_status(report.rows):
        raise ValueError("alert_status must match rows")
    if report.average_correlation_risk_score != _average(
        tuple(row.correlation_risk_score for row in report.rows),
    ):
        raise ValueError("average_correlation_risk_score must match rows")
    if report.max_correlation_risk_score != max(
        (row.correlation_risk_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_correlation_risk_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _pair_key(left_domain: str, right_domain: str) -> str:
    _require_domain("left_domain", left_domain)
    _require_domain("right_domain", right_domain)
    if left_domain == right_domain:
        raise ValueError("domains must be distinct")
    left_rank = _DOMAIN_RANK[left_domain]
    right_rank = _DOMAIN_RANK[right_domain]
    first, second = (
        (left_domain, right_domain)
        if left_rank < right_rank
        else (right_domain, left_domain)
    )
    return f"{first}__{second}"


def _normalize_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must contain supported values")
    normalized = tuple(reason for reason in _REASON_CODE_SEQUENCE if reason in value)
    if normalized != value:
        raise ValueError("reason_codes must be unique and sorted")
    status_reasons = tuple(
        reason
        for reason in value
        if reason
        in (
            "cross_domain_correlation_pass",
            "cross_domain_correlation_watch",
            "cross_domain_correlation_block",
        )
    )
    if len(status_reasons) != _ONE:
        raise ValueError("reason_codes must include exactly one alert status reason")
    if status_reasons == ("cross_domain_correlation_pass",) and len(value) != 1:
        raise ValueError("pass reason_codes cannot include risk reasons")
    return normalized


def _require_threshold_order(
    label: str,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if watch_threshold > block_threshold:
        raise ValueError(f"{label} watch threshold must not exceed block threshold")


def _require_alert_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _ALERT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_domain(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _DOMAIN_RANK:
        raise ValueError(f"{field_name} must be a supported public domain")
    _reject_unsafe_public_string(field_name, value)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized != value:
        raise ValueError(f"{field_name} must use the required decimal precision")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_signed_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < -_ONE or normalized > _ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return normalized


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT, rounding=ROUND_HALF_UP)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    value = _quantize(value)
    if value < _ZERO:
        return _ZERO
    if value > _ONE:
        return _ONE
    return value


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchCrossDomainCorrelationAlertReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _report_digest_from_values(values: dict[str, object]) -> str:
    payload = _json_ready(values)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) in (str, bool):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), allow_json_containers=True)
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError(f"{label} must be finite Decimal")
        return
    if isinstance(value, datetime):
        _as_utc(label, value)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError(f"{label} must not include float values")
    if type(value) is int:
        raise ValueError(f"{label} must use Decimal-derived numeric strings")
    if isinstance(value, dict):
        if not allow_json_containers:
            raise ValueError(f"{label} must not expose mutable mapping values")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_string("payload key", key)
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True in payload")
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{label} must not expose mutable sequence values")
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered:
        raise ValueError(f"{field_name} has unsafe value")
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe value")


__all__ = (
    "DEFAULT_RESEARCH_CROSS_DOMAIN_CORRELATION_ALERT_CONFIG_VERSION",
    "ResearchCrossDomainCorrelationAlertConfig",
    "ResearchCrossDomainCorrelationAlertObservation",
    "ResearchCrossDomainCorrelationAlertReport",
    "ResearchCrossDomainCorrelationAlertRow",
    "build_research_cross_domain_correlation_alert_report",
    "research_cross_domain_correlation_alert_payload",
)
