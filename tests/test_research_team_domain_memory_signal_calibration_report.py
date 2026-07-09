from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 11, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_domain_memory_signal_calibration_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def config(**overrides: object):
    module = api()
    return module.ResearchTeamDomainMemorySignalCalibrationConfig(**overrides)


def input_row(
    domain_label: str,
    team_label: str,
    signal_family_label: str,
    *,
    memory_sample_count: Decimal = d("150.000000"),
    calibrated_memory_count: Decimal = d("140.000000"),
    expected_signal_accuracy: Decimal = d("0.650000"),
    observed_signal_accuracy: Decimal = d("0.660000"),
    memory_age_seconds: Decimal = d("3600.000000"),
    disagreement_rate: Decimal = d("0.020000"),
    observed_at: datetime = OBSERVED_AT,
):
    module = api()
    return module.ResearchTeamDomainMemorySignalCalibrationInput(
        domain_label=domain_label,
        team_label=team_label,
        signal_family_label=signal_family_label,
        memory_sample_count=memory_sample_count,
        calibrated_memory_count=calibrated_memory_count,
        expected_signal_accuracy=expected_signal_accuracy,
        observed_signal_accuracy=observed_signal_accuracy,
        memory_age_seconds=memory_age_seconds,
        disagreement_rate=disagreement_rate,
        observed_at=observed_at,
    )


def build_report(*items, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_domain_memory_signal_calibration_report(
        items,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def test_team_domain_memory_signal_calibration_scores_rows_and_digest() -> None:
    rows = (
        input_row("sports_tennis", "team_match_results", "line_movement"),
        input_row(
            "macro_rates",
            "team_policy_events",
            "central_bank_timing",
            memory_sample_count=d("20.000000"),
            calibrated_memory_count=d("10.000000"),
            expected_signal_accuracy=d("0.650000"),
            observed_signal_accuracy=d("0.400000"),
            memory_age_seconds=d("900000.000000"),
            disagreement_rate=d("0.400000"),
        ),
        input_row(
            "weather_extremes",
            "team_forecast_models",
            "storm_track_shift",
            memory_sample_count=d("80.000000"),
            calibrated_memory_count=d("60.000000"),
            expected_signal_accuracy=d("0.650000"),
            observed_signal_accuracy=d("0.550000"),
            memory_age_seconds=d("172800.000000"),
            disagreement_rate=d("0.150000"),
        ),
    )

    report = build_report(*rows)
    reversed_report = build_report(*reversed(rows))

    assert api().DOMAIN_MEMORY_SIGNAL_CALIBRATION_STATUSES == ("pass", "watch", "block")
    assert report.status == "block"
    assert report.report_mode == "paper_domain_memory_signal_block"
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.watch_block_ratio == d("0.666667")
    assert report.min_memory_coverage_ratio == d("0.500000")
    assert report.max_signal_accuracy_gap_ratio == d("0.250000")
    assert report.max_memory_age_seconds == d("900000.000000")
    assert report.max_disagreement_rate == d("0.400000")
    assert report.max_calibration_pressure_score == d("1.000000")

    blocked, watched, passed = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.calibration_rank for row in report.rows) == (d("1"), d("2"), d("3"))
    assert blocked.domain_label == "macro_rates"
    assert blocked.memory_coverage_ratio == d("0.500000")
    assert blocked.signal_accuracy_gap_ratio == d("0.250000")
    assert blocked.memory_staleness_ratio == d("1.000000")
    assert blocked.calibration_pressure_score == d("1.000000")
    assert blocked.reason_codes == (
        "domain_memory_signal_coverage_block",
        "domain_memory_signal_accuracy_gap_block",
        "domain_memory_signal_staleness_block",
        "domain_memory_signal_disagreement_block",
    )
    assert watched.reason_codes == (
        "domain_memory_signal_coverage_watch",
        "domain_memory_signal_accuracy_gap_watch",
        "domain_memory_signal_staleness_watch",
        "domain_memory_signal_disagreement_watch",
    )
    assert passed.reason_codes == ("domain_memory_signal_calibration_pass",)
    assert (
        api().ResearchTeamDomainMemorySignalCalibrationReasonCodeCount(
            reason_code="domain_memory_signal_staleness_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        )
        in report.reason_code_counts
    )

    payload = api().research_team_domain_memory_signal_calibration_report_payload(report)
    reversed_payload = api().research_team_domain_memory_signal_calibration_report_payload(
        reversed_report,
    )

    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["rows"][0]["calibration_pressure_score"] == "1.000000"
    assert _float_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_team_domain_memory_signal_calibration_is_report_only_public_safe() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_SIGNAL_CALIBRATION_CONFIG_VERSION",
        "DOMAIN_MEMORY_SIGNAL_CALIBRATION_STATUSES",
        "ResearchTeamDomainMemorySignalCalibrationConfig",
        "ResearchTeamDomainMemorySignalCalibrationInput",
        "ResearchTeamDomainMemorySignalCalibrationReasonCodeCount",
        "ResearchTeamDomainMemorySignalCalibrationReport",
        "ResearchTeamDomainMemorySignalCalibrationRow",
        "build_research_team_domain_memory_signal_calibration_report",
        "research_team_domain_memory_signal_calibration_report_digest",
        "research_team_domain_memory_signal_calibration_report_payload",
    )

    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    empty = build_report()
    assert empty.status == "pass"
    assert empty.report_mode == "paper_domain_memory_signal_monitor"
    assert empty.reason_codes == ("domain_memory_signal_calibration_empty",)
    assert empty.input_count == ZERO
    assert empty.row_count == ZERO
    assert empty.reason_code_counts == ()
    assert empty.rows == ()

    populated = build_report(
        input_row("sports_tennis", "team_match_results", "line_movement"),
    )
    for value in (
        populated,
        *populated.rows,
        *populated.reason_code_counts,
        config(),
        input_row("macro_rates", "team_policy_events", "central_bank_timing"),
    ):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item is None:
                continue
            if field.name.endswith(("_count", "_ratio", "_score", "_seconds")):
                assert type(item) is Decimal

    with pytest.raises(FrozenInstanceError):
        populated.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(populated, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(populated, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="memory_sample_count must be a Decimal"):
        input_row("macro", "team_policy", "signal", memory_sample_count=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at must be UTC-aware"):
        input_row(
            "macro",
            "team_policy",
            "signal",
            observed_at=datetime(2026, 7, 9, 10, 0),
        )
    with pytest.raises(ValueError, match="generated_at must be UTC"):
        build_report(
            input_row("macro_rates", "team_policy", "central_bank_timing"),
            generated_at=datetime(
                2026,
                7,
                9,
                12,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        )
    with pytest.raises(ValueError, match="team-domain-signal labels must be unique"):
        build_report(
            input_row("macro_rates", "team_policy", "central_bank_timing"),
            input_row("macro_rates", "team_policy", "central_bank_timing"),
        )
    with pytest.raises(ValueError, match="observed_signal_accuracy"):
        input_row(
            "macro_rates",
            "team_policy",
            "central_bank_timing",
            observed_signal_accuracy=d("1.100000"),
        )
    with pytest.raises(ValueError, match="public aggregate label"):
        input_row("macro_market_ref", "team_policy", "central_bank_timing")
    with pytest.raises(ValueError, match="calibrated_memory_count"):
        input_row(
            "macro_rates",
            "team_policy",
            "central_bank_timing",
            memory_sample_count=d("10.000000"),
            calibrated_memory_count=d("11.000000"),
        )
    with pytest.raises(ValueError, match="min_watch_memory_coverage_ratio"):
        config(
            min_pass_memory_coverage_ratio=d("0.700000"),
            min_watch_memory_coverage_ratio=d("0.900000"),
        )

    payload = module.research_team_domain_memory_signal_calibration_report_payload(
        populated,
    )
    assert module.research_team_domain_memory_signal_calibration_report_digest(populated) == (
        payload["derived_validation_digest"]
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    for unsafe_key in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question_text",
        "source_url",
        "dsn",
        "table_name",
        "token",
        "wallet_ref",
        "order_ref",
        "trade_ref",
        "sizing_model",
        "recommendation",
    ):
        forged_payload = dict(payload)
        forged_payload[unsafe_key] = "public_aggregate"
        forged_payload["derived_validation_digest"] = canonical_digest(forged_payload)
        with pytest.raises(ValueError, match="public aggregate labels"):
            module.research_team_domain_memory_signal_calibration_report_payload(
                forged_payload,
            )

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def test_payload_validation_rejects_tampering_and_public_leaks() -> None:
    module = api()
    report = build_report(
        input_row("sports_tennis", "team_match_results", "line_movement"),
    )
    row = report.rows[0]

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            row,
            signal_accuracy_gap_ratio=d("0.100000"),
            derived_validation_digest=row.derived_validation_digest,
        )

    payload = module.research_team_domain_memory_signal_calibration_report_payload(report)

    tampered = dict(payload)
    tampered["status"] = "clear"
    tampered["derived_validation_digest"] = canonical_digest(tampered)
    with pytest.raises(ValueError, match="status"):
        module.research_team_domain_memory_signal_calibration_report_payload(tampered)

    leaked = dict(payload)
    leaked["rows"] = [dict(payload["rows"][0])]
    leaked["rows"][0]["domain_label"] = "market_slug"
    leaked["rows"][0]["derived_validation_digest"] = _row_digest(leaked["rows"][0])
    leaked["derived_validation_digest"] = canonical_digest(leaked)
    with pytest.raises(ValueError, match="public aggregate labels"):
        module.research_team_domain_memory_signal_calibration_report_payload(leaked)

    numeric = dict(payload)
    numeric["input_count"] = 1
    numeric["derived_validation_digest"] = canonical_digest(numeric)
    with pytest.raises(ValueError, match="numeric"):
        module.research_team_domain_memory_signal_calibration_report_payload(numeric)


def test_custom_watch_memory_window_drives_staleness_ratio() -> None:
    cfg = config(
        max_pass_memory_age_seconds=d("1800.000000"),
        max_watch_memory_age_seconds=d("7200.000000"),
    )

    report = build_report(
        input_row(
            "macro_rates",
            "team_policy",
            "central_bank_timing",
            memory_age_seconds=d("3600.000000"),
        ),
        cfg=cfg,
    )

    assert report.status == "watch"
    assert report.rows[0].status == "watch"
    assert report.rows[0].memory_staleness_ratio == d("0.500000")
    assert report.rows[0].reason_codes == (
        "domain_memory_signal_staleness_watch",
    )


def _row_digest(row_payload: dict[str, Any]) -> str:
    unsigned = dict(row_payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _float_paths(value: object, prefix: str = "$") -> tuple[str, ...]:
    if type(value) is float:
        return (prefix,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_float_paths(item, f"{prefix}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_float_paths(item, f"{prefix}[{index}]"))
        return tuple(paths)
    return ()
