from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "PaperForecastEnsembleQualityConfig",
    "PaperForecastEnsembleQualityModelDisagreement",
    "PaperForecastEnsembleQualityReport",
    "build_paper_forecast_ensemble_quality_report",
    "paper_forecast_ensemble_quality_payload",
)


RATIO_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0")
ONE = Decimal("1")
ZERO_COUNT = Decimal("0")
ONE_COUNT = Decimal("1")

ENSEMBLE_AGREEMENT_STATUSES = (
    "empty_forecast_ensemble",
    "single_model_only",
    "full_ensemble_agreement",
    "mixed_ensemble_agreement",
    "no_ensemble_agreement",
)
MODEL_DISAGREEMENT_STATUSES = (
    "model_disagreement_unavailable",
    "low_model_disagreement",
    "high_model_disagreement",
)
CONFIDENCE_CONCENTRATION_STATUSES = (
    "confidence_concentration_unavailable",
    "no_confidence_signal",
    "balanced_confidence",
    "concentrated_confidence",
)
_UNSAFE_PUBLIC_SURFACE_FRAGMENTS = frozenset(
    "".join(parts)
    for parts in (
        ("wal", "let"),
        ("or", "der"),
        ("acc", "ount"),
        ("au", "th"),
        ("li", "ve"),
        ("net", "work"),
        ("data", "base"),
        ("per", "sist"),
        ("trad", "ing"),
        ("tra", "de"),
        ("bro", "ker"),
        ("sign", "ing"),
        ("private", "_", "key"),
        ("api", "_", "key"),
        ("sec", "ret"),
        ("token",),
        ("http",),
        ("url",),
        ("uri",),
        ("post", "gres"),
        ("sql",),
    )
)


@dataclass(frozen=True)
class PaperForecastEnsembleQualityConfig:
    config_version: str = "forecast-ensemble-quality-v0"
    agreement_tolerance: Decimal = Decimal("0.050000")
    max_model_disagreement: Decimal = Decimal("0.150000")
    max_top_confidence_share: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("PaperForecastEnsembleQualityConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not PaperForecastEnsembleQualityConfig:
            raise ValueError("config must be exactly PaperForecastEnsembleQualityConfig")
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "agreement_tolerance",
            _require_probability("agreement_tolerance", self.agreement_tolerance),
        )
        object.__setattr__(
            self,
            "max_model_disagreement",
            _require_probability("max_model_disagreement", self.max_model_disagreement),
        )
        object.__setattr__(
            self,
            "max_top_confidence_share",
            _require_probability(
                "max_top_confidence_share",
                self.max_top_confidence_share,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class PaperForecastEnsembleQualityModelDisagreement:
    model_label: str
    basis: str
    fair_probability_yes: Decimal
    confidence: Decimal
    confidence_share: Decimal | None
    deviation_from_mean_probability: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperForecastEnsembleQualityModelDisagreement does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not PaperForecastEnsembleQualityModelDisagreement:
            raise ValueError(
                "row must be exactly PaperForecastEnsembleQualityModelDisagreement",
            )
        _require_canonical_string("model_label", self.model_label)
        _require_canonical_string("basis", self.basis)
        object.__setattr__(
            self,
            "fair_probability_yes",
            _require_probability("fair_probability_yes", self.fair_probability_yes),
        )
        object.__setattr__(
            self,
            "confidence",
            _require_probability("confidence", self.confidence),
        )
        object.__setattr__(
            self,
            "confidence_share",
            _require_optional_probability("confidence_share", self.confidence_share),
        )
        object.__setattr__(
            self,
            "deviation_from_mean_probability",
            _require_probability(
                "deviation_from_mean_probability",
                self.deviation_from_mean_probability,
            ),
        )
        _require_hard_flags("model disagreement row", self)


@dataclass(frozen=True)
class PaperForecastEnsembleQualityReport:
    generated_at: datetime
    config_version: str
    model_count: Decimal
    pair_count: Decimal
    mean_probability_yes: Decimal | None
    confidence_weighted_probability_yes: Decimal | None
    probability_range: Decimal | None
    mean_model_disagreement: Decimal | None
    max_model_disagreement: Decimal | None
    ensemble_agreement_share: Decimal | None
    ensemble_agreement_status: str
    model_disagreement_status: str
    top_confidence_share: Decimal | None
    confidence_concentration_index: Decimal | None
    confidence_concentration_status: str
    reason_codes: tuple[str, ...]
    model_disagreements: tuple[PaperForecastEnsembleQualityModelDisagreement, ...]
    derived_validation_digest: str = field(default="", init=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("PaperForecastEnsembleQualityReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not PaperForecastEnsembleQualityReport:
            raise ValueError("report must be exactly PaperForecastEnsembleQualityReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "model_count",
            _require_count_decimal("model_count", self.model_count),
        )
        object.__setattr__(
            self,
            "pair_count",
            _require_count_decimal("pair_count", self.pair_count),
        )
        for field_name in (
            "mean_probability_yes",
            "confidence_weighted_probability_yes",
            "probability_range",
            "mean_model_disagreement",
            "max_model_disagreement",
            "ensemble_agreement_share",
            "top_confidence_share",
            "confidence_concentration_index",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_probability(field_name, getattr(self, field_name)),
            )
        _require_member(
            "ensemble_agreement_status",
            self.ensemble_agreement_status,
            ENSEMBLE_AGREEMENT_STATUSES,
        )
        _require_member(
            "model_disagreement_status",
            self.model_disagreement_status,
            MODEL_DISAGREEMENT_STATUSES,
        )
        _require_member(
            "confidence_concentration_status",
            self.confidence_concentration_status,
            CONFIDENCE_CONCENTRATION_STATUSES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "model_disagreements",
            _normalize_model_disagreements(self.model_disagreements),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        object.__setattr__(
            self,
            "derived_validation_digest",
            _derived_validation_digest(asdict(self)),
        )
        _require_derived_validation_digest(self)
        _reject_unsafe_public_surface("report", self)


@dataclass(frozen=True)
class _ForecastRow:
    model_label: str
    basis: str
    fair_probability_yes: Decimal
    confidence: Decimal


def build_paper_forecast_ensemble_quality_report(
    forecasts: Iterable[object],
    *,
    config: PaperForecastEnsembleQualityConfig,
    generated_at: datetime,
) -> PaperForecastEnsembleQualityReport:
    if isinstance(forecasts, (str, bytes)):
        raise ValueError("forecasts must be an iterable")
    if type(config) is not PaperForecastEnsembleQualityConfig:
        raise ValueError("config must be PaperForecastEnsembleQualityConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    try:
        forecast_items = tuple(forecasts)
    except TypeError as exc:
        raise ValueError("forecasts must be an iterable") from exc

    rows = tuple(
        sorted(
            (_forecast_row(index, item) for index, item in enumerate(forecast_items)),
            key=lambda row: (row.basis, row.model_label),
        )
    )
    model_count = len(rows)
    pair_count = model_count * (model_count - 1) // 2
    probabilities = tuple(row.fair_probability_yes for row in rows)
    confidences = tuple(row.confidence for row in rows)

    mean_probability_yes = _mean(probabilities)
    total_confidence = sum(confidences, ZERO)
    confidence_shares = _confidence_shares(confidences, total_confidence)
    model_disagreements = _model_disagreement_rows(
        rows,
        mean_probability_yes,
        confidence_shares,
    )

    pair_distances = _pair_distances(probabilities)
    ensemble_agreement_share = _agreement_share(
        pair_distances,
        config.agreement_tolerance,
    )
    top_confidence_share = _top_confidence_share(confidence_shares)
    confidence_concentration_index = _confidence_concentration_index(confidence_shares)
    max_model_disagreement = _max_or_none(
        row.deviation_from_mean_probability for row in model_disagreements
    )
    ensemble_agreement_status = _ensemble_agreement_status(
        model_count,
        ensemble_agreement_share,
    )
    model_disagreement_status = _model_disagreement_status(
        model_count,
        max_model_disagreement,
        config,
    )
    confidence_concentration_status = _confidence_concentration_status(
        model_count,
        total_confidence,
        top_confidence_share,
        config,
    )

    return PaperForecastEnsembleQualityReport(
        generated_at=generated_at,
        config_version=config.config_version,
        model_count=_count(model_count),
        pair_count=_count(pair_count),
        mean_probability_yes=mean_probability_yes,
        confidence_weighted_probability_yes=_confidence_weighted_mean(
            rows,
            total_confidence,
            mean_probability_yes,
        ),
        probability_range=_probability_range(probabilities),
        mean_model_disagreement=_mean(
            tuple(row.deviation_from_mean_probability for row in model_disagreements),
        ),
        max_model_disagreement=max_model_disagreement,
        ensemble_agreement_share=ensemble_agreement_share,
        ensemble_agreement_status=ensemble_agreement_status,
        model_disagreement_status=model_disagreement_status,
        top_confidence_share=top_confidence_share,
        confidence_concentration_index=confidence_concentration_index,
        confidence_concentration_status=confidence_concentration_status,
        reason_codes=_reason_codes(
            model_count,
            ensemble_agreement_status,
            model_disagreement_status,
            confidence_concentration_status,
        ),
        model_disagreements=model_disagreements,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def paper_forecast_ensemble_quality_payload(
    report: PaperForecastEnsembleQualityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is PaperForecastEnsembleQualityReport:
        _require_hard_flags("report", report)
        _validate_report_consistency(report)
        _require_derived_validation_digest(report)
        _reject_unsafe_public_surface("report", report)
        payload = _payload_value(report, "report")
    elif type(report) is dict:
        _reject_unsafe_public_surface("payload", report)
        payload = _payload_value(report, "payload")
    else:
        raise ValueError("report must be a PaperForecastEnsembleQualityReport")
    if type(payload) is not dict:
        raise ValueError("payload must be a public report object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_surface("payload", payload)
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


def _forecast_row(index: int, value: object) -> _ForecastRow:
    _require_source_flags(index, value)
    _reject_unsafe_source_surface(index, value)
    fair_probability_yes = _require_probability(
        "fair_probability_yes",
        getattr(value, "fair_probability_yes", None),
    )
    confidence = _require_probability("confidence", getattr(value, "confidence", None))
    basis = getattr(value, "basis", None)
    _require_canonical_string("basis", basis)
    model_label = getattr(value, "model_name", None)
    if not isinstance(model_label, str) or not model_label.strip():
        model_label = basis
    _require_canonical_string("model_label", model_label)
    return _ForecastRow(
        model_label=model_label,
        basis=basis,
        fair_probability_yes=fair_probability_yes,
        confidence=confidence,
    )


def _require_source_flags(index: int, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"forecast {index} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"forecast {index} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"forecast {index} must be readonly")


def _model_disagreement_rows(
    rows: tuple[_ForecastRow, ...],
    mean_probability_yes: Decimal | None,
    confidence_shares: tuple[Decimal | None, ...],
) -> tuple[PaperForecastEnsembleQualityModelDisagreement, ...]:
    if mean_probability_yes is None:
        return ()
    output: list[PaperForecastEnsembleQualityModelDisagreement] = []
    for row, confidence_share in zip(rows, confidence_shares, strict=True):
        output.append(
            PaperForecastEnsembleQualityModelDisagreement(
                model_label=row.model_label,
                basis=row.basis,
                fair_probability_yes=row.fair_probability_yes,
                confidence=row.confidence,
                confidence_share=confidence_share,
                deviation_from_mean_probability=_absolute_decimal(
                    row.fair_probability_yes - mean_probability_yes,
                ),
                paper_only=True,
                report_only=True,
                readonly=True,
            )
        )
    return tuple(output)


def _pair_distances(values: tuple[Decimal, ...]) -> tuple[Decimal, ...]:
    distances: list[Decimal] = []
    for left_index, left in enumerate(values):
        for right in values[left_index + 1 :]:
            distances.append(_absolute_decimal(left - right))
    return tuple(distances)


def _agreement_share(
    pair_distances: tuple[Decimal, ...],
    agreement_tolerance: Decimal,
) -> Decimal | None:
    if not pair_distances:
        return None
    agreeing_pairs = sum(1 for distance in pair_distances if distance <= agreement_tolerance)
    return _quantize_ratio(Decimal(agreeing_pairs) / Decimal(len(pair_distances)))


def _confidence_shares(
    confidences: tuple[Decimal, ...],
    total_confidence: Decimal,
) -> tuple[Decimal | None, ...]:
    if not confidences:
        return ()
    if total_confidence == ZERO:
        return tuple(ZERO.quantize(RATIO_QUANTUM) for _ in confidences)
    return tuple(_quantize_ratio(confidence / total_confidence) for confidence in confidences)


def _confidence_weighted_mean(
    rows: tuple[_ForecastRow, ...],
    total_confidence: Decimal,
    mean_probability_yes: Decimal | None,
) -> Decimal | None:
    if not rows:
        return None
    if total_confidence == ZERO:
        return mean_probability_yes
    return _quantize_ratio(
        sum(
            (row.fair_probability_yes * row.confidence for row in rows),
            ZERO,
        )
        / total_confidence,
    )


def _probability_range(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _quantize_ratio(max(values) - min(values))


def _top_confidence_share(shares: tuple[Decimal | None, ...]) -> Decimal | None:
    if not shares:
        return None
    return _quantize_ratio(max(share for share in shares if share is not None))


def _confidence_concentration_index(shares: tuple[Decimal | None, ...]) -> Decimal | None:
    if not shares:
        return None
    return _quantize_ratio(sum((share * share for share in shares if share is not None), ZERO))


def _ensemble_agreement_status(
    model_count: int,
    ensemble_agreement_share: Decimal | None,
) -> str:
    if model_count == 0:
        return "empty_forecast_ensemble"
    if model_count == 1:
        return "single_model_only"
    if ensemble_agreement_share == ONE.quantize(RATIO_QUANTUM):
        return "full_ensemble_agreement"
    if ensemble_agreement_share and ensemble_agreement_share > ZERO:
        return "mixed_ensemble_agreement"
    return "no_ensemble_agreement"


def _model_disagreement_status(
    model_count: int,
    max_model_disagreement: Decimal | None,
    config: PaperForecastEnsembleQualityConfig,
) -> str:
    if model_count < 2 or max_model_disagreement is None:
        return "model_disagreement_unavailable"
    if max_model_disagreement > config.max_model_disagreement:
        return "high_model_disagreement"
    return "low_model_disagreement"


def _confidence_concentration_status(
    model_count: int,
    total_confidence: Decimal,
    top_confidence_share: Decimal | None,
    config: PaperForecastEnsembleQualityConfig,
) -> str:
    if model_count == 0:
        return "confidence_concentration_unavailable"
    if total_confidence == ZERO:
        return "no_confidence_signal"
    if top_confidence_share >= config.max_top_confidence_share:
        return "concentrated_confidence"
    return "balanced_confidence"


def _reason_codes(
    model_count: int,
    ensemble_agreement_status: str,
    model_disagreement_status: str,
    confidence_concentration_status: str,
) -> tuple[str, ...]:
    if model_count == 0:
        return ("no_forecasts",)
    confidence_reason = (
        "confidence_concentration_detected"
        if confidence_concentration_status == "concentrated_confidence"
        else confidence_concentration_status
    )
    return (
        ensemble_agreement_status,
        model_disagreement_status,
        confidence_reason,
    )


def _mean(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return _quantize_ratio(sum(items, ZERO) / Decimal(len(items)))


def _max_or_none(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return _quantize_ratio(max(items))


def _count(value: int) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("count must be a nonnegative integer")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _count_decimal_as_int(value: Decimal) -> int:
    return int(_require_count_decimal("count", value))


def _absolute_decimal(value: Decimal) -> Decimal:
    _require_finite_decimal("value", value)
    return _quantize_ratio(abs(value))


def _as_utc(field_name: str, value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative integer")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    return value


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return decimal_value


def _require_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_ratio(decimal_value)


def _require_optional_probability(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_probability(field_name, value)


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    normalized = decimal_value.quantize(COUNT_QUANTUM)
    if decimal_value != normalized:
        raise ValueError(f"{field_name} must be an integral Decimal")
    return normalized


def _require_member(
    field_name: str,
    value: str,
    allowed_values: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _normalize_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not items:
        raise ValueError(f"{field_name} must contain at least one value")
    for item in items:
        _require_canonical_string(field_name, item)
    return items


def _normalize_model_disagreements(
    value: object,
) -> tuple[PaperForecastEnsembleQualityModelDisagreement, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("model_disagreements must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("model_disagreements must be an iterable") from exc
    if not all(type(item) is PaperForecastEnsembleQualityModelDisagreement for item in items):
        raise ValueError(
            "model_disagreements must contain PaperForecastEnsembleQualityModelDisagreement values",
        )
    return items


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _validate_report_consistency(report: PaperForecastEnsembleQualityReport) -> None:
    model_count = _count_decimal_as_int(report.model_count)
    expected_model_count = _count(len(report.model_disagreements))
    if report.model_count != expected_model_count:
        raise ValueError("model_count must equal model_disagreements length")
    expected_pair_count = _count(model_count * (model_count - 1) // 2)
    if report.pair_count != expected_pair_count:
        raise ValueError("pair_count must match model_count")
    if report.model_count == ZERO_COUNT:
        if report.reason_codes != ("no_forecasts",):
            raise ValueError("reason_codes must match empty report")
        for field_name in (
            "mean_probability_yes",
            "confidence_weighted_probability_yes",
            "probability_range",
            "mean_model_disagreement",
            "max_model_disagreement",
            "ensemble_agreement_share",
            "top_confidence_share",
            "confidence_concentration_index",
        ):
            if getattr(report, field_name) is not None:
                raise ValueError(f"{field_name} must be absent without models")


def _derived_validation_digest(values: dict[str, object]) -> str:
    digest_payload = {
        key: _payload_value(item, key)
        for key, item in values.items()
        if key != "derived_validation_digest"
    }
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_derived_validation_digest(
    report: PaperForecastEnsembleQualityReport,
) -> None:
    _require_sha256_digest("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")


def _require_sha256_digest(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _payload_value(value: object, field_name: str) -> object:
    if type(value) in (
        PaperForecastEnsembleQualityConfig,
        PaperForecastEnsembleQualityModelDisagreement,
        PaperForecastEnsembleQualityReport,
    ):
        return _payload_value(asdict(value), field_name)
    if type(value) is Decimal:
        return str(_require_finite_decimal(field_name, value))
    if type(value) is datetime:
        return _as_utc(field_name, value).isoformat()
    if type(value) is dict:
        payload: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{field_name} keys must be strings")
            payload[key] = _payload_value(item, key)
        return payload
    if type(value) is tuple:
        return [_payload_value(item, field_name) for item in value]
    if type(value) is list:
        return [_payload_value(item, field_name) for item in value]
    if value is None or type(value) in (bool, str):
        return value
    if type(value) in (int, float):
        raise ValueError(f"{field_name} must be a Decimal")
    raise ValueError(f"unsafe public surface in {field_name}")


def _reject_unsafe_source_surface(index: int, value: object) -> None:
    if type(value) in (
        PaperForecastEnsembleQualityConfig,
        PaperForecastEnsembleQualityModelDisagreement,
        PaperForecastEnsembleQualityReport,
    ):
        _reject_unsafe_public_surface(f"forecast {index}", value)
        return
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        _reject_unsafe_public_surface(f"forecast {index}", asdict(value))
        return
    try:
        attrs = vars(value)
    except TypeError:
        return
    _reject_unsafe_public_surface(f"forecast {index}", attrs)


def _reject_unsafe_public_surface(label: str, payload: object) -> None:
    if type(payload) in (
        PaperForecastEnsembleQualityConfig,
        PaperForecastEnsembleQualityModelDisagreement,
        PaperForecastEnsembleQualityReport,
    ):
        _reject_unsafe_public_surface(label, asdict(payload))
        return
    if type(payload) is dict:
        for key, item in payload.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public surface in {label}")
            _reject_unsafe_text(f"{label} key", key)
            _reject_unsafe_public_surface(label, item)
        return
    if type(payload) in (list, tuple):
        for item in payload:
            _reject_unsafe_public_surface(label, item)
        return
    if type(payload) is str:
        _reject_unsafe_text(label, payload)
        return
    if (
        hasattr(payload, "__dataclass_fields__")
        and not isinstance(payload, type)
        and type(payload)
        not in (
            PaperForecastEnsembleQualityConfig,
            PaperForecastEnsembleQualityModelDisagreement,
            PaperForecastEnsembleQualityReport,
        )
    ):
        raise ValueError(f"unsafe public surface in {label}")


def _reject_unsafe_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in _UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
        raise ValueError(f"unsafe public surface in {label}")


def _quantize_ratio(value: Decimal) -> Decimal:
    _require_finite_decimal("ratio", value)
    return value.quantize(RATIO_QUANTUM)
