from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_source_reliability_playbook_v2",
    )


def _observation(
    source_family_id: str,
    *,
    team_id: str = "politics",
    source_family_label: str = "Official digest",
    source_family_updated_at: datetime = GENERATED_AT,
    historical_reliability_score: Decimal = d("1"),
    officialness_score: Decimal = d("1"),
    independence_score: Decimal = d("1"),
    median_latency_seconds: Decimal = d("0"),
    contradiction_rate: Decimal = d("0"),
    resolution_usefulness_score: Decimal = d("1"),
    evidence_count: Decimal = d("12"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    api = _api()
    return api.ResearchPacketSourceReliabilityPlaybookObservation(
        team_id=team_id,
        source_family_id=source_family_id,
        source_family_label=source_family_label,
        source_family_updated_at=source_family_updated_at,
        historical_reliability_score=historical_reliability_score,
        officialness_score=officialness_score,
        independence_score=independence_score,
        median_latency_seconds=median_latency_seconds,
        contradiction_rate=contradiction_rate,
        resolution_usefulness_score=resolution_usefulness_score,
        evidence_count=evidence_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _config(**overrides: object):
    api = _api()
    values = {
        "max_freshness_age_seconds": d("7200"),
        "max_latency_seconds": d("3600"),
        "min_historical_reliability_score": d("0.700000"),
        "min_freshness_score": d("0.500000"),
        "min_officialness_score": d("0.500000"),
        "min_independence_score": d("0.500000"),
        "min_latency_score": d("0.500000"),
        "max_contradiction_rate": d("0.200000"),
        "min_resolution_usefulness_score": d("0.500000"),
    }
    values.update(overrides)
    return api.ResearchPacketSourceReliabilityPlaybookConfig(**values)


def test_public_api_defaults_and_hard_readonly_flags() -> None:
    api = _api()

    assert api.DEFAULT_RESEARCH_PACKET_SOURCE_RELIABILITY_PLAYBOOK_CONFIG_VERSION == (
        "research-packet-source-reliability-playbook-v2"
    )
    assert api.__all__ == (
        "DEFAULT_RESEARCH_PACKET_SOURCE_RELIABILITY_PLAYBOOK_CONFIG_VERSION",
        "ResearchPacketSourceReliabilityPlaybookConfig",
        "ResearchPacketSourceReliabilityPlaybookObservation",
        "ResearchPacketSourceReliabilityPlaybookRow",
        "ResearchPacketSourceReliabilityPlaybookReasonCount",
        "ResearchPacketSourceReliabilityPlaybookReport",
        "build_research_packet_source_reliability_playbook_report",
        "research_packet_source_reliability_playbook_report_payload",
    )

    config = api.ResearchPacketSourceReliabilityPlaybookConfig()
    assert config.config_version == "research-packet-source-reliability-playbook-v2"
    assert config.max_freshness_age_seconds == d("86400")
    assert config.max_latency_seconds == d("3600")
    assert config.reliability_weight == d("1.000000")
    assert config.freshness_weight == d("1.000000")
    assert config.officialness_weight == d("1.000000")
    assert config.independence_weight == d("1.000000")
    assert config.latency_weight == d("1.000000")
    assert config.contradiction_weight == d("1.000000")
    assert config.resolution_usefulness_weight == d("1.000000")
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True

    with pytest.raises(FrozenInstanceError):
        config.readonly = False
    with pytest.raises(ValueError, match="config paper_only"):
        api.ResearchPacketSourceReliabilityPlaybookConfig(paper_only=False)
    with pytest.raises(ValueError, match="config_version"):
        api.ResearchPacketSourceReliabilityPlaybookConfig(
            config_version=_StringSubclass(
                "research-packet-source-reliability-playbook-v2",
            ),
        )
    with pytest.raises(ValueError, match="max_latency_seconds"):
        api.ResearchPacketSourceReliabilityPlaybookConfig(
            max_latency_seconds=3600,
        )


def test_playbook_report_ranks_source_families_by_team_and_reliability_inputs() -> None:
    api = _api()
    report = api.build_research_packet_source_reliability_playbook_report(
        observations=(
            _observation(
                "proxy_digest",
                source_family_label="Proxy digest",
                source_family_updated_at=GENERATED_AT - timedelta(seconds=3600),
                historical_reliability_score=d("0.500000"),
                officialness_score=d("0.500000"),
                independence_score=d("0.500000"),
                median_latency_seconds=d("1800"),
                contradiction_rate=d("0.500000"),
                resolution_usefulness_score=d("0.500000"),
            ),
            _observation("official_digest"),
            _observation(
                "reference_archive",
                team_id="sports",
                source_family_label="Reference archive",
                source_family_updated_at=GENERATED_AT - timedelta(seconds=9000),
                historical_reliability_score=d("0.400000"),
                officialness_score=d("0.400000"),
                independence_score=d("0.400000"),
                median_latency_seconds=d("5400"),
                contradiction_rate=d("0.300000"),
                resolution_usefulness_score=d("0.400000"),
                evidence_count=d("6"),
            ),
        ),
        config=_config(),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert isinstance(report, api.ResearchPacketSourceReliabilityPlaybookReport)
    assert report.generated_at == GENERATED_AT
    assert report.playbook_status == "watch"
    assert report.team_count == d("2")
    assert report.source_family_count == d("3")
    assert report.row_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("2")
    assert report.top_source_family_count == d("2")
    assert report.reason_codes == (
        "source_reliability_playbook_low_reliability",
        "source_reliability_playbook_stale_source_family",
        "source_reliability_playbook_low_officialness",
        "source_reliability_playbook_low_independence",
        "source_reliability_playbook_slow_source_family",
        "source_reliability_playbook_high_contradiction_rate",
        "source_reliability_playbook_low_resolution_usefulness",
    )
    assert tuple((row.team_id, row.rank, row.source_family_id) for row in report.rows) == (
        ("politics", d("1"), "official_digest"),
        ("politics", d("2"), "proxy_digest"),
        ("sports", d("1"), "reference_archive"),
    )

    top_row = report.rows[0]
    assert isinstance(top_row, api.ResearchPacketSourceReliabilityPlaybookRow)
    assert top_row.playbook_status == "pass"
    assert top_row.composite_reliability_score == d("1.000000")
    assert top_row.freshness_score == d("1.000000")
    assert top_row.latency_score == d("1.000000")
    assert top_row.contradiction_score == d("1.000000")
    assert top_row.reason_codes == ("source_reliability_playbook_passed",)

    proxy_row = report.rows[1]
    assert proxy_row.rank == d("2")
    assert proxy_row.composite_reliability_score == d("0.500000")
    assert proxy_row.freshness_score == d("0.500000")
    assert proxy_row.latency_score == d("0.500000")
    assert proxy_row.contradiction_score == d("0.500000")
    assert proxy_row.reason_codes == (
        "source_reliability_playbook_low_reliability",
        "source_reliability_playbook_high_contradiction_rate",
    )

    stale_row = report.rows[2]
    assert stale_row.playbook_status == "watch"
    assert stale_row.source_family_age_seconds == d("9000")
    assert stale_row.latency_score == d("0.000000")
    assert stale_row.reason_codes == (
        "source_reliability_playbook_low_reliability",
        "source_reliability_playbook_stale_source_family",
        "source_reliability_playbook_low_officialness",
        "source_reliability_playbook_low_independence",
        "source_reliability_playbook_slow_source_family",
        "source_reliability_playbook_high_contradiction_rate",
        "source_reliability_playbook_low_resolution_usefulness",
    )
    assert report.reason_code_counts == (
        api.ResearchPacketSourceReliabilityPlaybookReasonCount(
            reason_code="source_reliability_playbook_low_reliability",
            count=d("2"),
        ),
        api.ResearchPacketSourceReliabilityPlaybookReasonCount(
            reason_code="source_reliability_playbook_stale_source_family",
            count=d("1"),
        ),
        api.ResearchPacketSourceReliabilityPlaybookReasonCount(
            reason_code="source_reliability_playbook_low_officialness",
            count=d("1"),
        ),
        api.ResearchPacketSourceReliabilityPlaybookReasonCount(
            reason_code="source_reliability_playbook_low_independence",
            count=d("1"),
        ),
        api.ResearchPacketSourceReliabilityPlaybookReasonCount(
            reason_code="source_reliability_playbook_slow_source_family",
            count=d("1"),
        ),
        api.ResearchPacketSourceReliabilityPlaybookReasonCount(
            reason_code="source_reliability_playbook_high_contradiction_rate",
            count=d("2"),
        ),
        api.ResearchPacketSourceReliabilityPlaybookReasonCount(
            reason_code="source_reliability_playbook_low_resolution_usefulness",
            count=d("1"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_serializes_decimals_as_strings_and_digest_rejects_tampering() -> None:
    api = _api()
    report = api.build_research_packet_source_reliability_playbook_report(
        observations=(_observation("official_digest"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    payload = api.research_packet_source_reliability_playbook_report_payload(report)

    _assert_no_float(payload)
    assert payload["generated_at"] == "2026-07-02T12:00:00Z"
    assert payload["team_count"] == "1.000000"
    assert payload["rows"][0]["rank"] == "1.000000"
    assert payload["rows"][0]["composite_reliability_score"] == "1.000000"
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    assert json.loads(json.dumps(payload)) == payload
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, config_version="research-packet-source-reliability-playbook-v2b")
    with pytest.raises(ValueError, match="report"):
        api.research_packet_source_reliability_playbook_report_payload(object())


def test_frozen_decimal_only_contract_and_time_validation() -> None:
    api = _api()
    config = _config()
    observation = _observation("official_digest")

    with pytest.raises(FrozenInstanceError):
        observation.source_family_id = "other"
    with pytest.raises(ValueError, match="observation report_only"):
        replace(observation, report_only=False)
    with pytest.raises(ValueError, match="report readonly"):
        replace(
            api.build_research_packet_source_reliability_playbook_report(
                observations=(observation,),
                config=config,
                generated_at=GENERATED_AT,
            ),
            readonly=False,
        )
    with pytest.raises(ValueError, match="historical_reliability_score"):
        _observation("bad_decimal", historical_reliability_score=1)
    with pytest.raises(ValueError, match="officialness_score"):
        _observation("bad_subclass", officialness_score=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="generated_at"):
        api.build_research_packet_source_reliability_playbook_report(
            observations=(),
            config=config,
            generated_at=_DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        api.build_research_packet_source_reliability_playbook_report(
            observations=(),
            config=config,
            generated_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="future"):
        api.build_research_packet_source_reliability_playbook_report(
            observations=(
                _observation(
                    "future_family",
                    source_family_updated_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
            config=config,
            generated_at=GENERATED_AT,
        )

    report = api.build_research_packet_source_reliability_playbook_report(
        observations=(observation,),
        config=config,
        generated_at=GENERATED_AT,
    )
    for item in (config, observation, *report.rows, *report.reason_code_counts, report):
        _assert_decimal_public_metrics(item)


def test_row_rejects_report_level_empty_reason_code() -> None:
    api = _api()

    with pytest.raises(ValueError, match="empty reason"):
        api.ResearchPacketSourceReliabilityPlaybookRow(
            team_id="politics",
            rank=d("1"),
            source_family_id="official_digest",
            source_family_label="Official digest",
            source_family_updated_at=GENERATED_AT,
            source_family_age_seconds=d("0"),
            historical_reliability_score=d("1"),
            freshness_score=d("1"),
            officialness_score=d("1"),
            independence_score=d("1"),
            latency_score=d("1"),
            contradiction_rate=d("0"),
            contradiction_score=d("1"),
            resolution_usefulness_score=d("1"),
            composite_reliability_score=d("1"),
            evidence_count=d("12"),
            playbook_status="watch",
            reason_codes=("source_reliability_playbook_empty",),
        )


def test_unsafe_public_values_and_io_surfaces_are_rejected() -> None:
    api = _api()

    for unsafe_value in (
        "live_family",
        "auth_family",
        "wallet_family",
        "order_family",
        "network_family",
        "database_family",
        "persist_family",
        "signing_family",
        "mutation_family",
        "buy_family",
        "sell_family",
        "trade_family",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            _observation(unsafe_value)

    with pytest.raises(ValueError, match="unsafe public payload"):
        _observation("safe_family", source_family_label="trade notes")
    with pytest.raises(ValueError, match="unsafe public payload"):
        api.ResearchPacketSourceReliabilityPlaybookConfig(
            config_version="auth-version",
        )

    source = api.__loader__.get_source(api.__name__)
    assert source is not None
    tree = ast.parse(source)
    lowered_source = source.lower()
    forbidden_literals = (
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
    assert not any(token in lowered_source for token in forbidden_literals)

    imported_modules: set[str] = set()
    call_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            if call_name is not None:
                call_names.add(call_name.rsplit(".", maxsplit=1)[-1])

    forbidden_import_fragments = (
        "db",
        "env",
        "cli",
        "psycopg",
        "requests",
        "socket",
        "urllib",
        "http",
        "subprocess",
        "pathlib",
        "os",
    )
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "sign",
        "submit",
    }
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    assert not (call_names & forbidden_calls)


def _assert_no_float(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_float(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_float(item)


def _assert_decimal_public_metrics(value: object) -> None:
    for field in fields(value):
        field_value = getattr(value, field.name)
        if (
            field.name == "rank"
            or field.name.endswith("_count")
            or field.name.endswith("_rate")
            or field.name.endswith("_score")
            or field.name.endswith("_seconds")
            or field.name.endswith("_weight")
        ):
            if field_value is not None:
                assert type(field_value) is Decimal


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None
