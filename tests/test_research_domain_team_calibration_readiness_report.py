from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_domain_team_calibration_readiness_report.py"
)
GENERATED_AT = datetime(2026, 7, 12, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_domain_team_calibration_readiness_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": "research-domain-team-calibration-readiness-report-test",
        "min_pass_settled_count": d("20"),
        "min_watch_settled_count": d("8"),
        "max_pass_brier_score": d("0.160000"),
        "max_watch_brier_score": d("0.240000"),
        "max_pass_calibration_error": d("0.060000"),
        "max_watch_calibration_error": d("0.120000"),
        "min_pass_memory_coverage_ratio": d("0.800000"),
        "min_watch_memory_coverage_ratio": d("0.550000"),
    }
    values.update(overrides)
    return module.ResearchDomainTeamCalibrationReadinessConfig(**values)


def observation(**overrides: object) -> Any:
    module = api()
    values = {
        "domain_label": "macro-rates",
        "team_key": "rates-team",
        "settled_count": d("28"),
        "brier_score": d("0.120000"),
        "calibration_error": d("0.040000"),
        "memory_coverage_ratio": d("0.900000"),
    }
    values.update(overrides)
    return module.ResearchDomainTeamCalibrationReadinessObservation(**values)


def build_report(*observations: object, cfg: Any = None) -> Any:
    module = api()
    return module.build_research_domain_team_calibration_readiness_report(
        observations,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def assert_no_primitive_numbers(value: object) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"payload must not expose primitive numeric {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_primitive_numbers(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_no_primitive_numbers(item)


def test_builds_domain_team_calibration_readiness_report_with_status_mix() -> None:
    report = build_report(
        observation(
            domain_label="macro-rates",
            team_key="rates-alpha",
            settled_count=d("30"),
            brier_score=d("0.120000"),
            calibration_error=d("0.040000"),
            memory_coverage_ratio=d("0.900000"),
        ),
        observation(
            domain_label="crypto",
            team_key="btc-beta",
            settled_count=d("12"),
            brier_score=d("0.200000"),
            calibration_error=d("0.090000"),
            memory_coverage_ratio=d("0.620000"),
        ),
        observation(
            domain_label="sports",
            team_key="tennis-gamma",
            settled_count=d("6"),
            brier_score=d("0.280000"),
            calibration_error=d("0.180000"),
            memory_coverage_ratio=d("0.400000"),
        ),
    )

    assert type(report).__name__ == "ResearchDomainTeamCalibrationReadinessReport"
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.domain_team_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.settled_count == d("48")
    assert report.average_brier_score == d("0.200000")
    assert report.average_calibration_error == d("0.103333")
    assert report.average_memory_coverage_ratio == d("0.640000")
    assert report.lowest_memory_coverage_ratio == d("0.400000")
    assert report.reason_codes == (
        "domain_team_calibration_insufficient_settled_count_block",
        "domain_team_calibration_brier_score_block",
        "domain_team_calibration_error_block",
        "domain_team_calibration_memory_coverage_block",
        "domain_team_calibration_insufficient_settled_count_watch",
        "domain_team_calibration_brier_score_watch",
        "domain_team_calibration_error_watch",
        "domain_team_calibration_memory_coverage_watch",
        "domain_team_calibration_block",
        "domain_team_calibration_watch",
    )
    assert tuple((row.domain_label, row.team_key, row.status) for row in report.rows) == (
        ("macro-rates", "rates-alpha", "pass"),
        ("crypto", "btc-beta", "watch"),
        ("sports", "tennis-gamma", "block"),
    )
    assert report.rows[0].readiness_score == d("0.935000")
    assert report.rows[0].reason_codes == ("domain_team_calibration_ready",)
    assert report.rows[1].readiness_score == d("0.732500")
    assert report.rows[1].reason_codes == (
        "domain_team_calibration_insufficient_settled_count_watch",
        "domain_team_calibration_brier_score_watch",
        "domain_team_calibration_error_watch",
        "domain_team_calibration_memory_coverage_watch",
        "domain_team_calibration_watch",
    )
    assert report.rows[2].readiness_score == d("0.560000")
    assert report.rows[2].reason_codes == (
        "domain_team_calibration_insufficient_settled_count_block",
        "domain_team_calibration_brier_score_block",
        "domain_team_calibration_error_block",
        "domain_team_calibration_memory_coverage_block",
        "domain_team_calibration_block",
    )
    assert report.reason_code_counts[-2].reason_code == "domain_team_calibration_block"
    assert report.reason_code_counts[-2].count == d("1")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_empty_observation_set_blocks_report_only_summary() -> None:
    report = build_report()

    assert report.status == "block"
    assert report.domain_team_count == d("0")
    assert report.settled_count == d("0")
    assert report.average_brier_score is None
    assert report.average_calibration_error is None
    assert report.average_memory_coverage_ratio is None
    assert report.lowest_memory_coverage_ratio is None
    assert report.rows == ()
    assert report.reason_codes == ("domain_team_calibration_no_observations",)
    assert report.reason_code_counts[0].reason_code == (
        "domain_team_calibration_no_observations"
    )
    assert report.reason_code_counts[0].count == d("1")


def test_payload_is_deterministic_decimal_only_digest_bound_and_public_safe() -> None:
    module = api()
    first = build_report(observation(domain_label="sports", team_key="tennis-gamma"))
    second = build_report(observation(domain_label="sports", team_key="tennis-gamma"))

    assert second.derived_validation_digest == first.derived_validation_digest
    payload = module.research_domain_team_calibration_readiness_report_payload(first)
    assert module.research_domain_team_calibration_readiness_report_payload(payload) == payload
    assert payload["generated_at"] == "2026-07-12T12:00:00+00:00"
    assert payload["domain_team_count"] == "1"
    assert payload["average_brier_score"] == "0.120000"
    assert payload["rows"][0]["domain_label"] == "sports"
    assert payload["rows"][0]["readiness_score"] == "0.935000"
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_primitive_numbers(payload)

    encoded = json.dumps(payload, sort_keys=True)
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "private",
        "wallet",
        "order",
        "recommendation",
        "sizing",
        "http://",
        "https://",
    ):
        assert forbidden not in encoded.lower()

    tampered = dict(payload)
    tampered["average_brier_score"] = "0.130000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_domain_team_calibration_readiness_report_payload(tampered)

    unsafe = dict(payload)
    unsafe["source_url"] = "https://private.example/source"
    unsafe["derived_validation_digest"] = canonical_digest(unsafe)
    with pytest.raises(ValueError, match="unsafe"):
        module.research_domain_team_calibration_readiness_report_payload(unsafe)


def test_validation_rejects_non_decimal_duplicates_bad_thresholds_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_domain_team_calibration_readiness_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 12, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_domain_team_calibration_readiness_report(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 12, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="config"):
        module.build_research_domain_team_calibration_readiness_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="settled_count"):
        observation(settled_count=20)
    with pytest.raises(ValueError, match="brier_score"):
        observation(brier_score=0.1)
    with pytest.raises(ValueError, match="calibration_error"):
        observation(calibration_error=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="memory_coverage_ratio"):
        observation(memory_coverage_ratio=Decimal("NaN"))
    with pytest.raises(ValueError, match="domain_label"):
        observation(domain_label="https://private.example/domain")
    with pytest.raises(ValueError, match="watch threshold"):
        config(max_watch_brier_score=d("0.150000"))
    with pytest.raises(ValueError, match="watch threshold"):
        config(min_pass_memory_coverage_ratio=d("0.500000"))
    with pytest.raises(ValueError, match="observations"):
        build_report(object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="domain_label/team_key pairs must be unique"):
        build_report(observation(), observation())
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation(), paper_only=False)
    with pytest.raises(ValueError, match="average_brier_score"):
        replace(build_report(observation()), average_brier_score=d("0.130000"))
    with pytest.raises(TypeError):
        type(
            "ObservationSubclass",
            (module.ResearchDomainTeamCalibrationReadinessObservation,),
            {},
        )


def test_public_contract_is_frozen_decimal_only_report_only_and_in_memory() -> None:
    module = api()
    report = build_report(observation())

    for item in (
        config(),
        observation(),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    ):
        assert is_dataclass(item)
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_public_numeric_values_are_decimal(item)

    assert module.research_domain_team_calibration_readiness_report_digest(report) == (
        report.derived_validation_digest
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_DOMAIN_TEAM_CALIBRATION_READINESS_CONFIG_VERSION",
        "ResearchDomainTeamCalibrationReadinessConfig",
        "ResearchDomainTeamCalibrationReadinessObservation",
        "ResearchDomainTeamCalibrationReadinessReasonCodeCount",
        "ResearchDomainTeamCalibrationReadinessReport",
        "ResearchDomainTeamCalibrationReadinessRow",
        "build_research_domain_team_calibration_readiness_report",
        "research_domain_team_calibration_readiness_report_digest",
        "research_domain_team_calibration_readiness_report_payload",
    )

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: set[str] = set()
    calls: set[str] = set()
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            name = _call_name(node.func)
            if name is not None:
                calls.add(name)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    assert not float_constants
    assert not (
        imports
        & {
            "asyncio",
            "httpx",
            "os",
            "pathlib",
            "psycopg",
            "requests",
            "socket",
            "sqlite3",
            "subprocess",
            "supabase",
            "urllib",
        }
    )
    assert not (calls & {"__import__", "eval", "exec", "open", "print"})

    text = MODULE_PATH.read_text(encoding="utf-8").lower()
    for forbidden in (
        "database",
        "network",
        "credential",
        "private_key",
        "live",
        "trade",
        "broker",
        "buy",
        "sell",
        "request",
        "submit",
        "supabase",
        "sqlite",
        "postgres",
        "insert",
        "update",
        "delete",
        "commit",
        "cursor",
    ):
        assert forbidden not in text


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None
