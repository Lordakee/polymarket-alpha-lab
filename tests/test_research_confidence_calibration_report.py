from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
EXPECTED_EXPORTS = (
    "ResearchConfidenceCalibrationConfig",
    "ResearchConfidenceCalibrationInput",
    "ResearchConfidenceCalibrationReport",
    "ResearchConfidenceCalibrationRow",
    "build_research_confidence_calibration_report",
    "research_confidence_calibration_report_payload",
)
FORBIDDEN_IMPORT_PREFIXES = {
    "argparse",
    "os",
    "pathlib",
    "psycopg",
    "sqlite3",
    "sqlalchemy",
    "redis",
    "pymongo",
    "web3",
    "eth_account",
    "py_clob_client",
    "requests",
    "httpx",
    "aiohttp",
    "socket",
    "urllib",
    "http.client",
    "shelve",
    "pickle",
}
FORBIDDEN_PUBLIC_FRAGMENTS = (
    "candidate_id",
    "raw_candidate",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_ref",
    "source_url",
    "source_text",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommend",
)


def _module() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_confidence_calibration_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _input(
    prediction_key: str,
    *,
    domain_key: str = "macro_rates",
    confidence: Decimal = d("0.800000"),
    calibration: Decimal = d("0.850000"),
    drift: Decimal = d("0.050000"),
    difficulty: Decimal = d("0.250000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = _module()
    return module.ResearchConfidenceCalibrationInput(
        prediction_key=prediction_key,
        domain_key=domain_key,
        redacted_prediction_confidence=confidence,
        historical_calibration_score=calibration,
        recent_drift_score=drift,
        domain_difficulty_score=difficulty,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _bypassed_row(row: object, **overrides: Any) -> object:
    malformed = object.__new__(type(row))
    for key, value in row.__dict__.items():
        object.__setattr__(malformed, key, value)
    for key, value in overrides.items():
        object.__setattr__(malformed, key, value)
    return malformed


def _is_sha256_hex(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _assert_no_public_int_or_float_values(value: object) -> None:
    if type(value) in (float, int):
        pytest.fail("research confidence calibration report must expose Decimal-only numbers")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _assert_no_public_int_or_float_values(getattr(value, field.name))
    elif isinstance(value, dict):
        for key, item in value.items():
            _assert_no_public_int_or_float_values(key)
            _assert_no_public_int_or_float_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_public_int_or_float_values(item)


def _assert_public_payload_values(value: object) -> None:
    if isinstance(value, Decimal):
        pytest.fail("public payload must expose Decimal values as strings")
    if isinstance(value, datetime):
        pytest.fail("public payload must expose datetimes as strings")
    if type(value) in (float, int):
        pytest.fail("public payload must not expose numeric primitives")
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            _assert_public_payload_values(item)
    elif isinstance(value, list):
        for item in value:
            _assert_public_payload_values(item)
    elif isinstance(value, tuple):
        pytest.fail("public payload must expose arrays as lists")


def _assert_no_forbidden_public_surface(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            assert not any(fragment in lowered for fragment in FORBIDDEN_PUBLIC_FRAGMENTS)
            _assert_no_forbidden_public_surface(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_forbidden_public_surface(item)
    elif type(value) is str:
        lowered = value.lower()
        assert not any(fragment in lowered for fragment in FORBIDDEN_PUBLIC_FRAGMENTS)


def test_public_exports_are_exact_dataclasses_are_frozen_and_flags_are_hard() -> None:
    module = _module()

    assert module.__all__ == EXPECTED_EXPORTS

    config = module.ResearchConfidenceCalibrationConfig()
    input_row = _input("prediction-alpha")
    row = module.ResearchConfidenceCalibrationRow(
        prediction_key="prediction-alpha",
        domain_key="macro_rates",
        redacted_prediction_confidence=d("0.800000"),
        historical_calibration_score=d("0.850000"),
        recent_drift_score=d("0.050000"),
        domain_difficulty_score=d("0.250000"),
        confidence_calibration_score=d("0.837500"),
        status="pass",
        reason_codes=("research_confidence_calibration_pass",),
    )
    report = module.ResearchConfidenceCalibrationReport(
        generated_at=GENERATED_AT,
        config_version=config.config_version,
        input_count=d("1"),
        pass_count=d("1"),
        watch_count=d("0"),
        block_count=d("0"),
        average_confidence_calibration_score=d("0.837500"),
        max_recent_drift_score=d("0.050000"),
        max_domain_difficulty_score=d("0.250000"),
        status="pass",
        reason_codes=("research_confidence_calibration_pass",),
        rows=(row,),
    )

    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True
    assert input_row.paper_only is True
    assert row.report_only is True
    assert report.readonly is True
    assert _is_sha256_hex(row.derived_validation_digest)
    assert _is_sha256_hex(report.derived_validation_digest)
    _assert_no_public_int_or_float_values(report)

    with pytest.raises(FrozenInstanceError):
        config.config_version = "mutated"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        input_row.prediction_key = "mutated"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.input_count = d("0")  # type: ignore[misc]

    for cls in (
        module.ResearchConfidenceCalibrationConfig,
        module.ResearchConfidenceCalibrationInput,
        module.ResearchConfidenceCalibrationRow,
        module.ResearchConfidenceCalibrationReport,
    ):
        field_names = {field.name for field in fields(cls)}
        for field_name in field_names:
            lowered = field_name.lower()
            assert not any(
                fragment in lowered for fragment in FORBIDDEN_PUBLIC_FRAGMENTS
            )


def test_build_report_combines_confidence_calibration_drift_and_difficulty_into_pass_watch_block() -> None:
    module = _module()

    report = module.build_research_confidence_calibration_report(
        (
            _input(
                "prediction-watch",
                confidence=d("0.550000"),
                calibration=d("0.650000"),
                drift=d("0.200000"),
                difficulty=d("0.600000"),
            ),
            _input(
                "prediction-block",
                confidence=d("0.300000"),
                calibration=d("0.400000"),
                drift=d("0.350000"),
                difficulty=d("0.800000"),
            ),
            _input(
                "prediction-pass",
                confidence=d("0.800000"),
                calibration=d("0.850000"),
                drift=d("0.050000"),
                difficulty=d("0.250000"),
            ),
        ),
        config=module.ResearchConfidenceCalibrationConfig(
            config_version="research-confidence-calibration-report-test-v0",
            min_pass_prediction_confidence=d("0.600000"),
            min_watch_prediction_confidence=d("0.400000"),
            min_pass_historical_calibration=d("0.700000"),
            min_watch_historical_calibration=d("0.500000"),
            max_pass_recent_drift=d("0.150000"),
            max_watch_recent_drift=d("0.300000"),
            max_pass_domain_difficulty=d("0.500000"),
            max_watch_domain_difficulty=d("0.700000"),
        ),
        generated_at=datetime(2026, 7, 7, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert type(report) is module.ResearchConfidenceCalibrationReport
    assert report.generated_at == GENERATED_AT
    assert report.input_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.average_confidence_calibration_score == d("0.608333")
    assert report.max_recent_drift_score == d("0.350000")
    assert report.max_domain_difficulty_score == d("0.800000")
    assert report.status == "block"
    assert report.reason_codes == ("research_confidence_calibration_block",)

    block_row, pass_row, watch_row = report.rows
    assert block_row.prediction_key == "prediction-block"
    assert block_row.confidence_calibration_score == d("0.387500")
    assert block_row.status == "block"
    assert block_row.reason_codes == (
        "prediction_confidence_block",
        "historical_calibration_block",
        "recent_drift_block",
        "domain_difficulty_block",
    )

    assert pass_row.prediction_key == "prediction-pass"
    assert pass_row.confidence_calibration_score == d("0.837500")
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == ("research_confidence_calibration_pass",)

    assert watch_row.prediction_key == "prediction-watch"
    assert watch_row.confidence_calibration_score == d("0.600000")
    assert watch_row.status == "watch"
    assert watch_row.reason_codes == (
        "prediction_confidence_watch",
        "historical_calibration_watch",
        "recent_drift_watch",
        "domain_difficulty_watch",
    )
    _assert_no_public_int_or_float_values(report)


def test_report_can_return_watch_without_block_and_pass_without_findings() -> None:
    module = _module()
    config = module.ResearchConfidenceCalibrationConfig(
        config_version="research-confidence-calibration-report-test-v0",
    )

    watch_report = module.build_research_confidence_calibration_report(
        (
            _input(
                "prediction-watch",
                confidence=d("0.550000"),
                calibration=d("0.650000"),
                drift=d("0.200000"),
                difficulty=d("0.600000"),
            ),
        ),
        config=config,
        generated_at=GENERATED_AT,
    )
    pass_report = module.build_research_confidence_calibration_report(
        (_input("prediction-pass"),),
        config=config,
        generated_at=GENERATED_AT,
    )

    assert watch_report.status == "watch"
    assert watch_report.reason_codes == ("research_confidence_calibration_watch",)
    assert watch_report.watch_count == d("1")
    assert watch_report.block_count == d("0")
    assert pass_report.status == "pass"
    assert pass_report.reason_codes == ("research_confidence_calibration_pass",)
    assert pass_report.pass_count == d("1")


def test_dataclasses_reject_non_decimal_values_and_bad_hard_flags() -> None:
    module = _module()

    with pytest.raises(ValueError, match="min_pass_prediction_confidence"):
        module.ResearchConfidenceCalibrationConfig(min_pass_prediction_confidence=0.6)
    with pytest.raises(ValueError, match="max_watch_recent_drift"):
        module.ResearchConfidenceCalibrationConfig(max_watch_recent_drift=1)
    with pytest.raises(ValueError, match="paper_only"):
        module.ResearchConfidenceCalibrationConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        _input("prediction-alpha", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        module.ResearchConfidenceCalibrationRow(
            prediction_key="prediction-alpha",
            domain_key="macro_rates",
            redacted_prediction_confidence=d("0.800000"),
            historical_calibration_score=d("0.850000"),
            recent_drift_score=d("0.050000"),
            domain_difficulty_score=d("0.250000"),
            confidence_calibration_score=d("0.837500"),
            status="pass",
            reason_codes=("research_confidence_calibration_pass",),
            readonly=False,
        )
    with pytest.raises(ValueError, match="redacted_prediction_confidence"):
        _input("prediction-alpha", confidence=0.75)
    with pytest.raises(ValueError, match="input_count"):
        module.ResearchConfidenceCalibrationReport(
            generated_at=GENERATED_AT,
            config_version="research-confidence-calibration-report-test-v0",
            input_count=1,
            pass_count=d("1"),
            watch_count=d("0"),
            block_count=d("0"),
            average_confidence_calibration_score=d("0.837500"),
            max_recent_drift_score=d("0.050000"),
            max_domain_difficulty_score=d("0.250000"),
            status="pass",
            reason_codes=("research_confidence_calibration_pass",),
            rows=(),
        )


def test_build_report_rejects_bad_inputs_non_paper_inputs_and_leaky_research_surfaces() -> None:
    module = _module()
    config = module.ResearchConfidenceCalibrationConfig()
    input_row = _input("prediction-alpha")

    with pytest.raises(ValueError, match="inputs"):
        module.build_research_confidence_calibration_report(
            "not-inputs",
            config=config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="ResearchConfidenceCalibrationInput"):
        module.build_research_confidence_calibration_report(
            [object()],
            config=config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="paper_only"):
        module.build_research_confidence_calibration_report(
            [_bypassed_row(input_row, paper_only=False)],
            config=config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        module.build_research_confidence_calibration_report(
            [],
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_confidence_calibration_report(
            [],
            config=config,
            generated_at=None,
        )

    unsafe_inputs = (
        {"prediction_key": "raw_candidate_id:abc"},
        {"prediction_key": "market_slug:abc"},
        {"prediction_key": "source_ref:abc"},
        {"domain_key": "question:will-this"},
        {"domain_key": "wallet-auth-order"},
        {"domain_key": "buy_sell_recommendation"},
    )
    for overrides in unsafe_inputs:
        with pytest.raises(ValueError, match="unsafe public surface"):
            module.ResearchConfidenceCalibrationInput(
                prediction_key=overrides.get("prediction_key", "prediction-alpha"),
                domain_key=overrides.get("domain_key", "macro_rates"),
                redacted_prediction_confidence=d("0.800000"),
                historical_calibration_score=d("0.850000"),
                recent_drift_score=d("0.050000"),
                domain_difficulty_score=d("0.250000"),
            )


def test_public_payload_serializes_decimal_strings_rejects_leaks_and_validates_digest() -> None:
    module = _module()
    report = module.build_research_confidence_calibration_report(
        (_input("prediction-alpha"),),
        config=module.ResearchConfidenceCalibrationConfig(
            config_version="research-confidence-calibration-report-test-v0",
        ),
        generated_at=GENERATED_AT,
    )

    payload = module.research_confidence_calibration_report_payload(report)

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["input_count"] == "1"
    assert payload["pass_count"] == "1"
    assert payload["watch_count"] == "0"
    assert payload["block_count"] == "0"
    assert payload["average_confidence_calibration_score"] == "0.837500"
    assert payload["rows"][0]["redacted_prediction_confidence"] == "0.800000"
    assert payload["rows"][0]["confidence_calibration_score"] == "0.837500"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _is_sha256_hex(payload["derived_validation_digest"])
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert _is_sha256_hex(payload["rows"][0]["derived_validation_digest"])
    _assert_public_payload_values(payload)
    _assert_no_forbidden_public_surface(payload)
    assert module.research_confidence_calibration_report_payload(payload) == payload

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    tampered = dict(payload)
    tampered["pass_count"] = "99"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_confidence_calibration_report_payload(tampered)

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_confidence_calibration_report_payload(missing_digest)

    unsafe_payloads = (
        {**payload, "market_id": "redacted"},
        {**payload, "source_url": "redacted"},
        {**payload, "database_dsn": "redacted"},
        {**payload, "table_name": "redacted"},
        {**payload, "auth_token": "redacted"},
        {**payload, "wallet_address": "redacted"},
        {**payload, "order_id": "redacted"},
        {**payload, "trade_note": "redacted"},
        {**payload, "position_size": "redacted"},
        {**payload, "notes": "buy sell recommendation"},
    )
    for unsafe_payload in unsafe_payloads:
        with pytest.raises(ValueError, match="unsafe public surface"):
            module.research_confidence_calibration_report_payload(unsafe_payload)

    with pytest.raises(ValueError, match="ResearchConfidenceCalibrationReport"):
        module.research_confidence_calibration_report_payload(object())


def test_report_and_payload_digest_are_deterministic_across_input_order_and_decimal_scale() -> None:
    module = _module()
    config = module.ResearchConfidenceCalibrationConfig(
        config_version="research-confidence-calibration-report-test-v0",
    )

    first = module.build_research_confidence_calibration_report(
        (
            _input("prediction-beta", confidence=d("0.8000000")),
            _input("prediction-alpha", confidence=d("0.800000")),
        ),
        config=config,
        generated_at=GENERATED_AT,
    )
    second = module.build_research_confidence_calibration_report(
        (
            _input("prediction-alpha", confidence=d("0.800000")),
            _input("prediction-beta", confidence=d("0.800000")),
        ),
        config=config,
        generated_at=GENERATED_AT,
    )

    first_payload = module.research_confidence_calibration_report_payload(first)
    second_payload = module.research_confidence_calibration_report_payload(second)

    assert first == second
    assert first.derived_validation_digest == second.derived_validation_digest
    assert first_payload == second_payload
    assert first_payload["rows"][0]["prediction_key"] == "prediction-alpha"
    assert first_payload["rows"][1]["prediction_key"] == "prediction-beta"
    assert first_payload["input_count"] == "2"


def test_forbidden_imports_are_not_used_by_report_module() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_confidence_calibration_report.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.append(node.module)

    assert not {
        module_name
        for module_name in imported
        for prefix in FORBIDDEN_IMPORT_PREFIXES
        if module_name == prefix or module_name.startswith(f"{prefix}.")
    }
