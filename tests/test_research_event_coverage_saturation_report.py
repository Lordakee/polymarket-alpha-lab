from __future__ import annotations

import ast
import dataclasses
import json
from datetime import UTC, datetime, tzinfo
from decimal import Decimal
from importlib import import_module

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def _api():
    return import_module(
        "polymarket_alpha_lab.research_event_coverage_saturation_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object):
    api = _api()
    values = {
        "source_class_diversity_watch_floor": d("0.650000"),
        "source_class_diversity_block_floor": d("0.350000"),
        "fresh_evidence_max_age_seconds": d("3600"),
        "stale_evidence_block_age_seconds": d("21600"),
        "catalyst_cadence_watch_floor_per_day": d("1.000000"),
        "catalyst_cadence_block_floor_per_day": d("0.250000"),
        "team_capacity_watch_floor": d("0.550000"),
        "team_capacity_block_floor": d("0.250000"),
        "ambiguity_pressure_watch_threshold": d("0.400000"),
        "ambiguity_pressure_block_threshold": d("0.700000"),
    }
    values.update(overrides)
    return api.ResearchEventCoverageSaturationConfig(**values)


def _subject(
    coverage_bucket: str = "macro-policy-cluster",
    *,
    source_class_diversity_score: Decimal = d("0.820000"),
    freshest_evidence_age_seconds: Decimal = d("900"),
    catalyst_cadence_per_day: Decimal = d("3.000000"),
    team_capacity_score: Decimal = d("0.860000"),
    ambiguity_pressure_score: Decimal = d("0.100000"),
):
    api = _api()
    return api.ResearchEventCoverageSaturationSubject(
        coverage_bucket=coverage_bucket,
        source_class_diversity_score=source_class_diversity_score,
        freshest_evidence_age_seconds=freshest_evidence_age_seconds,
        catalyst_cadence_per_day=catalyst_cadence_per_day,
        team_capacity_score=team_capacity_score,
        ambiguity_pressure_score=ambiguity_pressure_score,
    )


def _report(subjects: tuple[object, ...], *, cfg=None, generated_at=GENERATED_AT):
    api = _api()
    return api.build_research_event_coverage_saturation_report(
        subjects,
        generated_at=generated_at,
        config=cfg or _config(),
    )


def test_empty_input_returns_public_report_only_pass_report() -> None:
    api = _api()
    report = _report(())

    assert report == api.ResearchEventCoverageSaturationReport(
        generated_at=GENERATED_AT,
        config_version="research-event-coverage-saturation-report-v0",
        coverage_bucket_count=d("0"),
        pass_count=d("0"),
        watch_count=d("0"),
        block_count=d("0"),
        average_coverage_saturation_score=d("0.000000"),
        min_coverage_saturation_score=d("0.000000"),
        min_source_class_diversity_score=d("0.000000"),
        max_freshest_evidence_age_seconds=d("0"),
        min_catalyst_cadence_per_day=d("0.000000"),
        min_team_capacity_score=d("0.000000"),
        max_ambiguity_pressure_score=d("0.000000"),
        status="pass",
        reason_code_counts=(),
        rows=(),
        derived_payload_digest=report.derived_payload_digest,
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_payload_digest) == 64


def test_scores_source_age_catalyst_capacity_and_ambiguity_pressure() -> None:
    api = _api()
    report = _report(
        (
            _subject("pass-bucket"),
            _subject(
                "watch-bucket",
                source_class_diversity_score=d("0.500000"),
                freshest_evidence_age_seconds=d("7200"),
                catalyst_cadence_per_day=d("0.600000"),
                team_capacity_score=d("0.450000"),
                ambiguity_pressure_score=d("0.500000"),
            ),
            _subject(
                "block-bucket",
                source_class_diversity_score=d("0.200000"),
                freshest_evidence_age_seconds=d("30000"),
                catalyst_cadence_per_day=d("0.100000"),
                team_capacity_score=d("0.100000"),
                ambiguity_pressure_score=d("0.800000"),
            ),
        ),
    )

    assert tuple(row.coverage_bucket for row in report.rows) == (
        "block-bucket",
        "watch-bucket",
        "pass-bucket",
    )
    assert [row.status for row in report.rows] == ["block", "watch", "pass"]
    assert report.coverage_bucket_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.status == "block"
    assert report.average_coverage_saturation_score == d("0.523667")
    assert report.min_coverage_saturation_score == d("0.120000")
    assert report.min_source_class_diversity_score == d("0.200000")
    assert report.max_freshest_evidence_age_seconds == d("30000")
    assert report.min_catalyst_cadence_per_day == d("0.100000")
    assert report.min_team_capacity_score == d("0.100000")
    assert report.max_ambiguity_pressure_score == d("0.800000")

    block_row, watch_row, pass_row = report.rows
    assert block_row.coverage_saturation_score == d("0.120000")
    assert block_row.reason_codes == (
        "low_source_class_diversity_block",
        "stale_evidence_age_block",
        "thin_catalyst_cadence_block",
        "constrained_team_capacity_block",
        "high_ambiguity_pressure_block",
    )
    assert watch_row.coverage_saturation_score == d("0.543333")
    assert watch_row.reason_codes == (
        "low_source_class_diversity_watch",
        "aging_evidence_watch",
        "thin_catalyst_cadence_watch",
        "constrained_team_capacity_watch",
        "elevated_ambiguity_pressure_watch",
    )
    assert pass_row.coverage_saturation_score == d("0.907667")
    assert pass_row.reason_codes == ("coverage_saturation_clear",)

    reason_counts = dict(report.reason_code_counts)
    assert reason_counts["stale_evidence_age_block"] == d("1")
    assert reason_counts["aging_evidence_watch"] == d("1")

    payload = api.research_event_coverage_saturation_report_payload(report)
    rendered = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "buy",
        "sell",
        "recommend",
        "position",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "event_id",
        "market_id",
        "source_id",
        "slug",
        "condition_id",
    ):
        assert forbidden not in rendered


def test_payload_digest_is_deterministic_and_decimal_string_only() -> None:
    api = _api()
    subjects = (
        _subject("z-bucket", source_class_diversity_score=d("0.660000")),
        _subject("a-bucket", catalyst_cadence_per_day=d("0.100000")),
        _subject("m-bucket", ambiguity_pressure_score=d("0.800000")),
    )

    report = _report(subjects)
    reversed_report = _report(tuple(reversed(subjects)))
    payload = api.research_event_coverage_saturation_report_payload(report)

    assert reversed_report.rows == report.rows
    assert reversed_report.derived_payload_digest == report.derived_payload_digest
    assert len(report.derived_payload_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_payload_digest)
    assert payload["derived_payload_digest"] == report.derived_payload_digest
    assert payload["coverage_bucket_count"] == "3"
    assert payload["rows"][0]["catalyst_cadence_per_day"] == "0.100000"
    assert payload["rows"][0]["coverage_saturation_score"] == "0.727667"
    assert payload["reason_code_counts"][0][1] == "1"
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, Decimal) for value in _walk_values(payload))
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert not any(type(value) is int for value in _walk_values(payload))
    assert api.research_event_coverage_saturation_report_payload(payload) == payload

    tampered_payload = dict(payload)
    tampered_payload["coverage_bucket_count"] = "4"
    with pytest.raises(ValueError, match="derived_payload_digest"):
        api.research_event_coverage_saturation_report_payload(tampered_payload)


def test_dataclasses_are_frozen_decimal_only_utc_and_flag_guarded() -> None:
    report = _report((_subject(),))

    with pytest.raises(dataclasses.FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        dataclasses.replace(_config(), paper_only=False)
    with pytest.raises(ValueError, match="Decimal"):
        _config(source_class_diversity_watch_floor=_DecimalSubclass("0.650000"))
    with pytest.raises(ValueError, match="Decimal"):
        _subject(source_class_diversity_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        _subject(freshest_evidence_age_seconds=900)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="public aggregate bucket"):
        _subject("raw-event-id-123")
    with pytest.raises(ValueError, match="duplicate"):
        _report((_subject("dup-bucket"), _subject("dup-bucket")))
    with pytest.raises(ValueError, match="generated_at"):
        _report((_subject(),), generated_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC))
    with pytest.raises(ValueError, match="timezone-aware"):
        _report((_subject(),), generated_at=datetime(2026, 7, 8, 12))
    with pytest.raises(ValueError, match="UTC offset"):
        _report(
            (_subject(),),
            generated_at=datetime(2026, 7, 8, 12, tzinfo=_NoneOffsetTimezone()),
        )


def test_module_does_not_expose_database_network_or_execution_surface() -> None:
    api = _api()
    source = inspectable_source(api)
    tree = ast.parse(source)

    forbidden_imports = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "web3",
        "py_clob_client",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "executemany",
        "open",
        "post",
        "put",
        "patch",
        "delete",
        "request",
        "send",
        "submit",
        "create_order",
        "cancel_order",
        "place_order",
    }
    forbidden_assigned_fragments = ("wallet", "auth", "order", "trade", "live")

    imported_roots: set[str] = set()
    called_names: set[str] = set()
    assigned_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id.lower())
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr.lower())
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigned_names.add(target.id.lower())

    assert forbidden_imports.isdisjoint(imported_roots)
    assert forbidden_calls.isdisjoint(called_names)
    assert not any(
        fragment in name
        for fragment in forbidden_assigned_fragments
        for name in assigned_names
    )


def inspectable_source(module: object) -> str:
    import inspect

    return inspect.getsource(module)


def _walk_values(value: object) -> tuple[object, ...]:
    values: list[object] = [value]
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_values(item))
    elif isinstance(value, list | tuple):
        for item in value:
            values.extend(_walk_values(item))
    return tuple(values)
