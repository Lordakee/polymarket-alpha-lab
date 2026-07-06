from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import inspect
from pathlib import Path

import pytest

import polymarket_alpha_lab.forecast_ensemble_quality as feq
from polymarket_alpha_lab.forecast_ensemble_quality import (
    PaperForecastEnsembleQualityConfig,
    PaperForecastEnsembleQualityModelDisagreement,
    PaperForecastEnsembleQualityReport,
    build_paper_forecast_ensemble_quality_report,
    paper_forecast_ensemble_quality_payload,
)


GENERATED_AT = datetime(2026, 10, 2, 15, 30, tzinfo=UTC)


@dataclass(frozen=True)
class ForecastOutput:
    fair_probability_yes: Decimal
    confidence: Decimal
    basis: str
    model_name: str = "model-a"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    market_slug: str = "must-not-leak"
    question: str = "Will this field leak?"


@dataclass(frozen=True)
class UnsafeForecastSurface:
    fair_probability_yes: Decimal
    confidence: Decimal
    basis: str
    model_name: str
    wallet_address: str = "0xabc"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def _config(**overrides: object) -> PaperForecastEnsembleQualityConfig:
    values = {
        "config_version": "ensemble-quality-test",
        "agreement_tolerance": Decimal("0.050000"),
        "max_model_disagreement": Decimal("0.150000"),
        "max_top_confidence_share": Decimal("0.600000"),
    }
    values.update(overrides)
    return PaperForecastEnsembleQualityConfig(**values)


def test_build_paper_forecast_ensemble_quality_report_summarizes_agreement():
    report = build_paper_forecast_ensemble_quality_report(
        (
            ForecastOutput(
                fair_probability_yes=Decimal("0.6100"),
                confidence=Decimal("0.6000"),
                basis="llm_glm_v0",
                model_name="glm-4-flash",
            ),
            ForecastOutput(
                fair_probability_yes=Decimal("0.6400"),
                confidence=Decimal("0.3000"),
                basis="book_imbalance_v0",
                model_name="book-depth",
            ),
            ForecastOutput(
                fair_probability_yes=Decimal("0.5800"),
                confidence=Decimal("0.1000"),
                basis="calibration_prior_v0",
                model_name="calibration",
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, PaperForecastEnsembleQualityReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "ensemble-quality-test"
    assert report.model_count == Decimal("3")
    assert report.pair_count == Decimal("3")
    assert report.mean_probability_yes == Decimal("0.610000")
    assert report.confidence_weighted_probability_yes == Decimal("0.616000")
    assert report.probability_range == Decimal("0.060000")
    assert report.mean_model_disagreement == Decimal("0.020000")
    assert report.max_model_disagreement == Decimal("0.030000")
    assert report.ensemble_agreement_share == Decimal("0.666667")
    assert report.ensemble_agreement_status == "mixed_ensemble_agreement"
    assert report.model_disagreement_status == "low_model_disagreement"
    assert report.top_confidence_share == Decimal("0.600000")
    assert report.confidence_concentration_index == Decimal("0.460000")
    assert report.confidence_concentration_status == "concentrated_confidence"
    assert report.reason_codes == (
        "mixed_ensemble_agreement",
        "low_model_disagreement",
        "confidence_concentration_detected",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64
    assert all(char in "0123456789abcdef" for char in report.derived_validation_digest)

    assert tuple(row.model_label for row in report.model_disagreements) == (
        "book-depth",
        "calibration",
        "glm-4-flash",
    )
    assert tuple(row.basis for row in report.model_disagreements) == (
        "book_imbalance_v0",
        "calibration_prior_v0",
        "llm_glm_v0",
    )
    assert tuple(row.deviation_from_mean_probability for row in report.model_disagreements) == (
        Decimal("0.030000"),
        Decimal("0.030000"),
        Decimal("0.000000"),
    )


def test_forecast_ensemble_quality_sorts_model_rows_deterministically():
    report = build_paper_forecast_ensemble_quality_report(
        (
            ForecastOutput(
                fair_probability_yes=Decimal("0.6400"),
                confidence=Decimal("0.3000"),
                basis="zeta_basis",
                model_name="zeta-model",
            ),
            ForecastOutput(
                fair_probability_yes=Decimal("0.6100"),
                confidence=Decimal("0.6000"),
                basis="alpha_basis",
                model_name="alpha-model",
            ),
            ForecastOutput(
                fair_probability_yes=Decimal("0.5800"),
                confidence=Decimal("0.1000"),
                basis="alpha_basis",
                model_name="alpha-backup",
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert tuple(
        (row.basis, row.model_label) for row in report.model_disagreements
    ) == (
        ("alpha_basis", "alpha-backup"),
        ("alpha_basis", "alpha-model"),
        ("zeta_basis", "zeta-model"),
    )


def test_report_does_not_emit_market_slug_question_or_advice_fields():
    report = build_paper_forecast_ensemble_quality_report(
        (
            ForecastOutput(
                fair_probability_yes=Decimal("0.5200"),
                confidence=Decimal("0.5000"),
                basis="llm_glm_v0",
                model_name="llm",
            ),
            ForecastOutput(
                fair_probability_yes=Decimal("0.5300"),
                confidence=Decimal("0.5000"),
                basis="book_imbalance_v0",
                model_name="book",
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    report_field_names = {field.name for field in fields(report)}
    model_field_names = {field.name for field in fields(report.model_disagreements[0])}
    assert "market_slug" not in report_field_names | model_field_names
    assert "question" not in report_field_names | model_field_names
    assert "recommended_next_step" not in report_field_names
    assert "advice" not in report_field_names

    payload_text = repr(asdict(report))
    assert "must-not-leak" not in payload_text
    assert "Will this field leak?" not in payload_text


def test_empty_and_single_model_inputs_are_readonly_quality_summaries():
    empty_report = build_paper_forecast_ensemble_quality_report(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    assert empty_report.model_count == 0
    assert empty_report.model_count == Decimal("0")
    assert empty_report.pair_count == Decimal("0")
    assert empty_report.mean_probability_yes is None
    assert empty_report.ensemble_agreement_status == "empty_forecast_ensemble"
    assert empty_report.model_disagreement_status == "model_disagreement_unavailable"
    assert empty_report.confidence_concentration_status == "confidence_concentration_unavailable"
    assert empty_report.reason_codes == ("no_forecasts",)

    single_report = build_paper_forecast_ensemble_quality_report(
        (
            ForecastOutput(
                fair_probability_yes=Decimal("0.5200"),
                confidence=Decimal("0.7000"),
                basis="llm_glm_v0",
                model_name="llm",
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    assert single_report.model_count == Decimal("1")
    assert single_report.pair_count == Decimal("0")
    assert single_report.mean_probability_yes == Decimal("0.520000")
    assert single_report.ensemble_agreement_status == "single_model_only"
    assert single_report.model_disagreement_status == "model_disagreement_unavailable"
    assert single_report.top_confidence_share == Decimal("1.000000")


def test_forecast_ensemble_quality_rejects_float_and_nonpaper_inputs():
    with pytest.raises(ValueError, match="fair_probability_yes must be a Decimal"):
        build_paper_forecast_ensemble_quality_report(
            (
                ForecastOutput(
                    fair_probability_yes=0.52,  # type: ignore[arg-type]
                    confidence=Decimal("0.7000"),
                    basis="llm_glm_v0",
                    model_name="llm",
                ),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="forecast 0 must be paper_only"):
        build_paper_forecast_ensemble_quality_report(
            (
                ForecastOutput(
                    fair_probability_yes=Decimal("0.5200"),
                    confidence=Decimal("0.7000"),
                    basis="llm_glm_v0",
                    model_name="llm",
                    paper_only=False,
                ),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_config_and_reports_are_frozen_and_hard_flagged():
    config = _config()
    with pytest.raises(FrozenInstanceError):
        config.config_version = "mutated"  # type: ignore[misc]
    with pytest.raises(ValueError, match="config paper_only must be True"):
        replace(config, paper_only=False)

    report = build_paper_forecast_ensemble_quality_report(
        (
            ForecastOutput(
                fair_probability_yes=Decimal("0.5200"),
                confidence=Decimal("0.7000"),
                basis="llm_glm_v0",
                model_name="llm",
            ),
        ),
        config=config,
        generated_at=GENERATED_AT,
    )
    with pytest.raises(FrozenInstanceError):
        report.model_count = 99  # type: ignore[misc]
    with pytest.raises(ValueError, match="report readonly must be True"):
        replace(report, readonly=False)

    row = report.model_disagreements[0]
    assert is_dataclass(row)
    with pytest.raises(FrozenInstanceError):
        row.confidence = Decimal("0.100000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="model disagreement row report_only must be True"):
        replace(row, report_only=False)

    class DerivedDecimal(Decimal):
        pass

    with pytest.raises(ValueError, match="agreement_tolerance must be a Decimal"):
        _config(agreement_tolerance=DerivedDecimal("0.010000"))


def test_public_payload_serializes_decimal_strings_and_revalidates_digest():
    report = build_paper_forecast_ensemble_quality_report(
        (
            ForecastOutput(
                fair_probability_yes=Decimal("0.5200"),
                confidence=Decimal("0.5000"),
                basis="llm_glm_v0",
                model_name="llm",
            ),
            ForecastOutput(
                fair_probability_yes=Decimal("0.5300"),
                confidence=Decimal("0.5000"),
                basis="book_imbalance_v0",
                model_name="book",
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    payload = paper_forecast_ensemble_quality_payload(report)

    assert payload["generated_at"] == "2026-10-02T15:30:00+00:00"
    assert payload["model_count"] == "2"
    assert payload["pair_count"] == "1"
    assert payload["mean_probability_yes"] == "0.525000"
    assert payload["top_confidence_share"] == "0.500000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["model_disagreements"][0]["fair_probability_yes"] == "0.530000"
    assert payload["model_disagreements"][0]["confidence_share"] == "0.500000"

    payload_text = repr(payload)
    assert "Decimal(" not in payload_text
    assert "must-not-leak" not in payload_text
    assert "Will this field leak?" not in payload_text

    object.__setattr__(report, "model_count", Decimal("99"))
    with pytest.raises(ValueError, match="derived_validation_digest|model_count"):
        paper_forecast_ensemble_quality_payload(report)


def test_payload_accepts_plain_readonly_dicts_and_rejects_numeric_or_unsafe_surfaces():
    payload = paper_forecast_ensemble_quality_payload(
        {
            "generated_at": GENERATED_AT,
            "model_count": Decimal("1"),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )

    assert payload["generated_at"] == "2026-10-02T15:30:00+00:00"
    assert payload["model_count"] == "1"

    for unsafe_payload in (
        {"wallet_address": "0xabc", "paper_only": True, "report_only": True, "readonly": True},
        {"note": "submit a live order", "paper_only": True, "report_only": True, "readonly": True},
        {"network_url": "https://example.invalid", "paper_only": True, "report_only": True, "readonly": True},
        {"database_uri": "postgres://example", "paper_only": True, "report_only": True, "readonly": True},
        {"persist_path": "/tmp/example", "paper_only": True, "report_only": True, "readonly": True},
        {"auth_token": "redacted", "paper_only": True, "report_only": True, "readonly": True},
    ):
        with pytest.raises(ValueError, match="unsafe public surface"):
            paper_forecast_ensemble_quality_payload(unsafe_payload)

    with pytest.raises(ValueError, match="model_count must be a Decimal"):
        paper_forecast_ensemble_quality_payload(
            {"model_count": 1, "paper_only": True, "report_only": True, "readonly": True},
        )

    with pytest.raises(ValueError, match="paper_only"):
        paper_forecast_ensemble_quality_payload(
            {"paper_only": False, "report_only": True, "readonly": True},
        )


def test_forecast_input_rejects_unsafe_source_surface_fields():
    with pytest.raises(ValueError, match="unsafe public surface"):
        build_paper_forecast_ensemble_quality_report(
            (
                UnsafeForecastSurface(
                    fair_probability_yes=Decimal("0.5200"),
                    confidence=Decimal("0.7000"),
                    basis="llm_glm_v0",
                    model_name="llm",
                ),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_forecast_ensemble_quality_scope_stays_phase_1_and_readonly():
    source = Path("src/polymarket_alpha_lab/forecast_ensemble_quality.py").read_text(
        encoding="utf-8",
    )
    parsed_source = ast.parse(source)

    for forbidden in (
        "fast",
        "wallet",
        "order",
        "account",
        "auth",
        "live",
        "network",
        "database",
        "persist",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "sqlite",
        "subprocess",
        "Path",
        "open(",
        "market_slug",
        "question",
    ):
        assert forbidden not in source

    assert feq.__all__ == (
        "PaperForecastEnsembleQualityConfig",
        "PaperForecastEnsembleQualityModelDisagreement",
        "PaperForecastEnsembleQualityReport",
        "build_paper_forecast_ensemble_quality_report",
        "paper_forecast_ensemble_quality_payload",
    )
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(parsed_source)
    )

    imported_roots: set[str] = set()
    for node in ast.walk(parsed_source):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
    forbidden_call_names = {
        "__import__",
        "connect",
        "execute",
        "float",
        "open",
        "request",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(parsed_source):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names

    assert inspect.getsource(PaperForecastEnsembleQualityModelDisagreement) in source
