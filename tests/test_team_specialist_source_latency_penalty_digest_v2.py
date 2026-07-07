from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
import importlib
import inspect
import json
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 15, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_source_latency_penalty_digest_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "median_watch_latency_seconds": d("900.000000"),
        "median_block_latency_seconds": d("1800.000000"),
        "p95_watch_latency_seconds": d("1800.000000"),
        "p95_block_latency_seconds": d("3600.000000"),
        "stale_source_watch_ratio": d("0.200000"),
        "stale_source_block_ratio": d("0.500000"),
        "refresh_watch_age_seconds": d("1200.000000"),
        "refresh_block_age_seconds": d("3600.000000"),
    }
    values.update(overrides)
    return module.TeamSpecialistSourceLatencyPenaltyDigestV2Config(**values)


def latency_input(
    team_id: str,
    domain: str,
    *,
    median: str,
    p95: str,
    stale: str,
    sources: str,
    refresh_age_seconds: int,
):
    module = api()
    return module.TeamSpecialistSourceLatencyPenaltyInputV2(
        team_id=team_id,
        domain=domain,
        median_source_latency_seconds=d(median),
        p95_source_latency_seconds=d(p95),
        stale_source_count=d(stale),
        source_count=d(sources),
        latest_refresh_at=GENERATED_AT - timedelta(seconds=refresh_age_seconds),
    )


def build_report(*items: object, cfg: object | None = None):
    module = api()
    return module.build_team_specialist_source_latency_penalty_digest_v2(
        items,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


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
    if type(value) is dict:
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_float_values(item)
    if type(value) in (list, tuple):
        for item in value:
            assert_no_float_values(item)


def test_scores_team_domain_latency_penalties_and_rolls_up_report_counts() -> None:
    module = api()

    report = build_report(
        latency_input(
            "team-beta",
            "sports.baseball",
            median="600.000000",
            p95="1200.000000",
            stale="0",
            sources="5",
            refresh_age_seconds=300,
        ),
        latency_input(
            "team-alpha",
            "finance.macro",
            median="1200.000000",
            p95="2400.000000",
            stale="1",
            sources="4",
            refresh_age_seconds=1500,
        ),
        latency_input(
            "team-alpha",
            "crypto.defi",
            median="2200.000000",
            p95="4200.000000",
            stale="3",
            sources="4",
            refresh_age_seconds=4200,
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        module.DEFAULT_TEAM_SPECIALIST_SOURCE_LATENCY_PENALTY_DIGEST_V2_CONFIG_VERSION
    )
    assert report.report_status == "block"
    assert report.team_domain_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.high_latency_count == d("2")
    assert report.stale_source_count == d("2")
    assert report.stale_refresh_count == d("2")
    assert report.max_latency_penalty_score == d("1.000000")
    assert report.reason_codes == (
        "latency_penalty_high",
        "stale_source_ratio_watch",
        "stale_source_ratio_block",
        "refresh_age_watch",
        "refresh_age_block",
    )
    assert report.reason_code_counts == (
        module.TeamSpecialistSourceLatencyPenaltyReasonCodeCountV2(
            reason_code="latency_penalty_high",
            count=d("2"),
        ),
        module.TeamSpecialistSourceLatencyPenaltyReasonCodeCountV2(
            reason_code="stale_source_ratio_watch",
            count=d("1"),
        ),
        module.TeamSpecialistSourceLatencyPenaltyReasonCodeCountV2(
            reason_code="stale_source_ratio_block",
            count=d("1"),
        ),
        module.TeamSpecialistSourceLatencyPenaltyReasonCodeCountV2(
            reason_code="refresh_age_watch",
            count=d("1"),
        ),
        module.TeamSpecialistSourceLatencyPenaltyReasonCodeCountV2(
            reason_code="refresh_age_block",
            count=d("1"),
        ),
    )

    crypto, macro, baseball = report.rows
    assert (crypto.team_id, crypto.domain) == ("team-alpha", "crypto.defi")
    assert crypto.latency_penalty_score == d("1.000000")
    assert crypto.stale_source_ratio == d("0.750000")
    assert crypto.refresh_age_seconds == d("4200.000000")
    assert crypto.status == "block"
    assert crypto.reason_codes == (
        "median_latency_block",
        "p95_latency_block",
        "latency_penalty_high",
        "stale_source_ratio_block",
        "refresh_age_block",
    )

    assert (macro.team_id, macro.domain) == ("team-alpha", "finance.macro")
    assert macro.latency_penalty_score == d("0.666667")
    assert macro.stale_source_ratio == d("0.250000")
    assert macro.refresh_age_seconds == d("1500.000000")
    assert macro.status == "watch"
    assert macro.reason_codes == (
        "median_latency_watch",
        "p95_latency_watch",
        "latency_penalty_high",
        "stale_source_ratio_watch",
        "refresh_age_watch",
    )

    assert (baseball.team_id, baseball.domain) == ("team-beta", "sports.baseball")
    assert baseball.latency_penalty_score == d("0.333333")
    assert baseball.stale_source_ratio == d("0.000000")
    assert baseball.refresh_age_seconds == d("300.000000")
    assert baseball.status == "pass"
    assert baseball.reason_codes == ("latency_penalty_pass",)

    assert all(len(row.derived_validation_digest) == 64 for row in report.rows)
    assert len(report.derived_validation_digest) == 64
    assert_public_numeric_values_are_decimal(report)


def test_digest_and_payload_are_input_order_deterministic_and_tamper_evident() -> None:
    module = api()
    first_item = latency_input(
        "team-alpha",
        "finance.macro",
        median="1200.000000",
        p95="2400.000000",
        stale="1",
        sources="4",
        refresh_age_seconds=1500,
    )
    second_item = latency_input(
        "team-beta",
        "sports.baseball",
        median="600.000000",
        p95="1200.000000",
        stale="0",
        sources="5",
        refresh_age_seconds=300,
    )

    first = build_report(second_item, first_item)
    second = build_report(first_item, second_item)

    assert first.rows == second.rows
    assert first.derived_validation_digest == second.derived_validation_digest

    payload = module.team_specialist_source_latency_penalty_digest_v2_payload(first)
    assert payload["generated_at"] == "2026-07-07T15:30:00+00:00"
    assert payload["team_domain_count"] == "2"
    assert payload["rows"][0]["latency_penalty_score"] == "0.666667"
    assert payload["rows"][0]["derived_validation_digest"] == (
        first.rows[0].derived_validation_digest
    )
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)
    json.loads(json.dumps(payload, sort_keys=True))

    tampered = dict(payload)
    tampered["block_count"] = "9"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.team_specialist_source_latency_penalty_digest_v2_payload(tampered)

    object.__setattr__(first.rows[0], "latency_penalty_score", d("0.000001"))
    with pytest.raises(ValueError, match="derived_validation_digest|tamper"):
        module.team_specialist_source_latency_penalty_digest_v2_payload(first)

    with pytest.raises(ValueError, match="Decimal"):
        module.team_specialist_source_latency_penalty_digest_v2_payload(
            {"score": 1, "paper_only": True, "report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="float"):
        module.team_specialist_source_latency_penalty_digest_v2_payload(
            {"score": 0.5, "paper_only": True, "report_only": True, "readonly": True},
        )


def test_empty_input_returns_empty_report_status_and_zero_decimals() -> None:
    module = api()

    report = build_report()

    assert report.report_status == "empty"
    assert report.team_domain_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.high_latency_count == d("0")
    assert report.stale_source_count == d("0")
    assert report.stale_refresh_count == d("0")
    assert report.max_latency_penalty_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("latency_penalty_digest_empty",)
    assert report.reason_code_counts == (
        module.TeamSpecialistSourceLatencyPenaltyReasonCodeCountV2(
            reason_code="latency_penalty_digest_empty",
            count=d("1"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert_public_numeric_values_are_decimal(report)


def test_dataclasses_validate_decimals_datetimes_counts_flags_and_frozen_instances() -> None:
    module = api()
    item = latency_input(
        "team-alpha",
        "finance.macro",
        median="1200.000000",
        p95="2400.000000",
        stale="1",
        sources="4",
        refresh_age_seconds=1500,
    )
    report = build_report(item)

    for value in (config(), item, report.rows[0], report.reason_code_counts[0], report):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        assert_public_numeric_values_are_decimal(value)
        with pytest.raises(FrozenInstanceError):
            value.readonly = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(item, paper_only=False)
    with pytest.raises(ValueError, match="median_source_latency_seconds"):
        latency_input(
            "team-alpha",
            "finance.macro",
            median="-1.000000",
            p95="2400.000000",
            stale="1",
            sources="4",
            refresh_age_seconds=1500,
        )
    with pytest.raises(ValueError, match="source_count"):
        latency_input(
            "team-alpha",
            "finance.macro",
            median="1200.000000",
            p95="2400.000000",
            stale="5",
            sources="4",
            refresh_age_seconds=1500,
        )
    with pytest.raises(ValueError, match="latest_refresh_at must be timezone-aware"):
        module.TeamSpecialistSourceLatencyPenaltyInputV2(
            team_id="team-alpha",
            domain="finance.macro",
            median_source_latency_seconds=d("1200.000000"),
            p95_source_latency_seconds=d("2400.000000"),
            stale_source_count=d("1"),
            source_count=d("4"),
            latest_refresh_at=datetime(2026, 7, 7, 15, 0),
        )
    with pytest.raises(ValueError, match="source_count"):
        latency_input(
            "team-alpha",
            "finance.macro",
            median="1200.000000",
            p95="2400.000000",
            stale="0",
            sources="0",
            refresh_age_seconds=1500,
        )
    with pytest.raises(ValueError, match="stale_source_count"):
        module.TeamSpecialistSourceLatencyPenaltyInputV2(
            team_id="team-alpha",
            domain="finance.macro",
            median_source_latency_seconds=d("1200.000000"),
            p95_source_latency_seconds=d("2400.000000"),
            stale_source_count=d("1.5"),
            source_count=d("4"),
            latest_refresh_at=GENERATED_AT - timedelta(seconds=1500),
        )
    with pytest.raises(ValueError, match="median_watch_latency_seconds"):
        config(median_watch_latency_seconds=_DecimalSubclass("900.000000"))

    class MissingOffsetTz(tzinfo):
        def utcoffset(self, dt):  # type: ignore[no-untyped-def]
            return None

        def dst(self, dt):  # type: ignore[no-untyped-def]
            return None

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_team_specialist_source_latency_penalty_digest_v2(
            (item,),
            config=config(),
            generated_at=datetime(2026, 7, 7, 15, 30, tzinfo=MissingOffsetTz()),
        )
    with pytest.raises(ValueError, match="latest_refresh_at must not be in the future"):
        build_report(
            module.TeamSpecialistSourceLatencyPenaltyInputV2(
                team_id="team-alpha",
                domain="finance.macro",
                median_source_latency_seconds=d("1200.000000"),
                p95_source_latency_seconds=d("2400.000000"),
                stale_source_count=d("1"),
                source_count=d("4"),
                latest_refresh_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )


@pytest.mark.parametrize(
    "unsafe_value",
    (
        "li" "ve_surface",
        "au" "th_surface",
        "wal" "let_surface",
        "or" "der_surface",
        "net" "work_surface",
        "data" "base_surface",
        "per" "sist_surface",
        "sig" "ning_surface",
        "mu" "tation_surface",
        "b" "uy_surface",
        "se" "ll_surface",
        "tra" "de_surface",
    ),
)
def test_rejects_unsafe_public_keys_and_values(unsafe_value: str) -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public"):
        latency_input(
            unsafe_value,
            "finance.macro",
            median="1200.000000",
            p95="2400.000000",
            stale="1",
            sources="4",
            refresh_age_seconds=1500,
        )
    with pytest.raises(ValueError, match="unsafe public"):
        module.team_specialist_source_latency_penalty_digest_v2_payload(
            {"note": unsafe_value, "paper_only": True, "report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="unsafe public"):
        module.team_specialist_source_latency_penalty_digest_v2_payload(
            {unsafe_value: "redacted", "paper_only": True, "report_only": True, "readonly": True},
        )


def test_module_scope_has_no_unsafe_surfaces() -> None:
    module = api()
    source_text = inspect.getsource(module)
    tree = ast.parse(source_text)

    assert module.__all__ == (
        "DEFAULT_TEAM_SPECIALIST_SOURCE_LATENCY_PENALTY_DIGEST_V2_CONFIG_VERSION",
        "REPORT_STATUSES",
        "ROW_STATUSES",
        "TeamSpecialistSourceLatencyPenaltyDigestV2Config",
        "TeamSpecialistSourceLatencyPenaltyInputV2",
        "TeamSpecialistSourceLatencyPenaltyReasonCodeCountV2",
        "TeamSpecialistSourceLatencyPenaltyRowV2",
        "TeamSpecialistSourceLatencyPenaltyReportV2",
        "build_team_specialist_source_latency_penalty_digest_v2",
        "team_specialist_source_latency_penalty_digest_v2_payload",
    )
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
    forbidden_source_terms = (
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "postgres",
        "sqlite",
        "au" "th",
        "wal" "let",
        "or" "der",
        "net" "work",
        "data" "base",
        "per" "sist",
        "sig" "ning",
        "mu" "tation",
        "b" "uy",
        "se" "ll",
        "tra" "de",
        "tra" "ding",
        "broker",
        "client",
        "execute",
        "connect",
        "subprocess",
        "open(",
        "pathlib",
        "wri" "te_text",
        "wri" "te_bytes",
    )
    assert all(term not in source_text.lower() for term in forbidden_source_terms)

    forbidden_call_names = {
        "__import__",
        "connect",
        "execute",
        "float",
        "open",
        "request",
        "send",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names
