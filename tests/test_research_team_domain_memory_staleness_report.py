from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_domain_memory_staleness_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_domain_memory_staleness_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            "research-team-domain-memory-staleness-report-test"
        ),
        "stale_after_seconds": d("7776000.000000"),
        "block_stale_after_seconds": d("15552000.000000"),
        "stale_outcome_feedback_after_seconds": d("3888000.000000"),
        "min_recent_outcome_feedback_count": d("2.000000"),
        "min_pass_memory_coverage_ratio": d("0.700000"),
        "min_watch_memory_coverage_ratio": d("0.400000"),
        "min_pass_calibration_score": d("0.700000"),
        "min_watch_calibration_score": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainMemoryStalenessConfig(**values)


def observation(**overrides: object):
    module = api()
    values = {
        "domain_category": "politics",
        "team_key": "policy-team",
        "memory_updated_at": GENERATED_AT - timedelta(days=10),
        "last_outcome_feedback_at": GENERATED_AT - timedelta(days=5),
        "memory_coverage_ratio": d("0.850000"),
        "calibration_score": d("0.820000"),
        "settled_outcome_count": d("10.000000"),
        "recent_outcome_feedback_count": d("3.000000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainMemoryStalenessObservation(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_domain_memory_staleness_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def walk(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk(nested))
    if isinstance(value, list):
        return tuple(item for nested in value for item in walk(nested))
    return (value,)


def assert_no_float_values(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is Decimal:
        return
    if isinstance(value, datetime):
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


def assert_public_payload_has_no_forbidden_surface(value: object) -> None:
    forbidden = (
        "raw",
        "candidate_id",
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "http://",
        "https://",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "table",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "trading",
        "buy",
        "sell",
        "recommend",
        "position",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lower_key = str(key).lower()
            assert not any(fragment in lower_key for fragment in forbidden), lower_key
            assert_public_payload_has_no_forbidden_surface(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_payload_has_no_forbidden_surface(item)
        return
    if isinstance(value, str):
        lower_value = value.lower()
        assert not any(fragment in lower_value for fragment in forbidden), lower_value


def test_public_api_declares_report_only_contract() -> None:
    module = api()

    assert module.DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_STALENESS_REPORT_CONFIG_VERSION == (
        "research-team-domain-memory-staleness-report-v0"
    )
    assert module.PUBLIC_DOMAIN_CATEGORIES == (
        "politics",
        "crypto",
        "equities",
        "commodities",
        "football",
        "basketball",
        "other",
    )
    assert module.PUBLIC_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_STALENESS_REPORT_CONFIG_VERSION",
        "PUBLIC_DOMAIN_CATEGORIES",
        "PUBLIC_STATUSES",
        "ResearchTeamDomainMemoryStalenessConfig",
        "ResearchTeamDomainMemoryStalenessObservation",
        "ResearchTeamDomainMemoryStalenessRow",
        "ResearchTeamDomainMemoryStalenessReport",
        "build_research_team_domain_memory_staleness_report",
        "research_team_domain_memory_staleness_report_payload",
        "research_team_domain_memory_staleness_report_digest",
    )

    field_defaults = {
        field.name: field.default
        for field in fields(module.ResearchTeamDomainMemoryStalenessConfig)
    }
    assert field_defaults["paper_only"] is True
    assert field_defaults["report_only"] is True
    assert field_defaults["readonly"] is True


def test_builds_pass_watch_block_and_missing_category_rows() -> None:
    report = build_report(
        observation(domain_category="politics", team_key="policy-team"),
        observation(
            domain_category="politics",
            team_key="legal-team",
            memory_coverage_ratio=d("0.750000"),
            calibration_score=d("0.880000"),
            recent_outcome_feedback_count=d("2.000000"),
        ),
        observation(
            domain_category="crypto",
            team_key="onchain-team",
            memory_updated_at=GENERATED_AT - timedelta(days=120),
            last_outcome_feedback_at=GENERATED_AT - timedelta(days=20),
            memory_coverage_ratio=d("0.600000"),
            calibration_score=d("0.650000"),
            settled_outcome_count=d("12.000000"),
            recent_outcome_feedback_count=d("2.000000"),
        ),
        observation(
            domain_category="equities",
            team_key="index-team",
            memory_updated_at=GENERATED_AT - timedelta(days=220),
            last_outcome_feedback_at=None,
            memory_coverage_ratio=d("0.300000"),
            calibration_score=d("0.400000"),
            settled_outcome_count=d("8.000000"),
            recent_outcome_feedback_count=d("0.000000"),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.public_status == "block"
    assert report.category_count == d("7.000000")
    assert report.observed_category_count == d("3.000000")
    assert report.missing_category_count == d("4.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("5.000000")
    assert report.stale_category_count == d("2.000000")
    assert report.under_calibrated_category_count == d("2.000000")
    assert report.missing_recent_outcome_feedback_category_count == d("1.000000")
    assert report.average_memory_coverage_ratio == d("0.566667")
    assert report.average_calibration_score == d("0.633333")
    assert report.max_oldest_memory_age_seconds == d("19008000.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    rows = {row.domain_category: row for row in report.rows}
    assert tuple(rows) == (
        "basketball",
        "commodities",
        "equities",
        "football",
        "other",
        "crypto",
        "politics",
    )
    assert rows["politics"].public_status == "pass"
    assert rows["politics"].team_count == d("2.000000")
    assert rows["politics"].memory_coverage_ratio == d("0.800000")
    assert rows["politics"].average_calibration_score == d("0.850000")
    assert rows["politics"].recent_outcome_feedback_count == d("5.000000")
    assert rows["politics"].reason_codes == (
        "research_team_domain_memory_staleness_healthy_memory",
    )

    assert rows["crypto"].public_status == "watch"
    assert rows["crypto"].oldest_memory_age_seconds == d("10368000.000000")
    assert rows["crypto"].reason_codes == (
        "research_team_domain_memory_staleness_stale_memory",
        "research_team_domain_memory_staleness_low_memory_coverage",
        "research_team_domain_memory_staleness_under_calibrated",
    )

    assert rows["equities"].public_status == "block"
    assert rows["equities"].newest_outcome_feedback_age_seconds is None
    assert rows["equities"].reason_codes == (
        "research_team_domain_memory_staleness_block_stale_memory",
        "research_team_domain_memory_staleness_block_memory_coverage",
        "research_team_domain_memory_staleness_block_under_calibrated",
        "research_team_domain_memory_staleness_missing_recent_outcome_feedback",
    )

    assert rows["basketball"].public_status == "block"
    assert rows["basketball"].team_count == d("0.000000")
    assert rows["basketball"].reason_codes == (
        "research_team_domain_memory_staleness_missing_domain_memory",
    )
    assert rows["basketball"].validation_digest.startswith("sha256:")

    assert report.reason_codes == (
        "research_team_domain_memory_staleness_report_block_present",
        "research_team_domain_memory_staleness_report_watch_present",
        "research_team_domain_memory_staleness_report_missing_domain_memory_present",
        "research_team_domain_memory_staleness_report_stale_memory_present",
        "research_team_domain_memory_staleness_report_under_calibrated_present",
        "research_team_domain_memory_staleness_report_missing_outcome_feedback_present",
        "research_team_domain_memory_staleness_report_healthy_memory_present",
    )
    assert report.validation_digest.startswith("sha256:")


def test_empty_report_blocks_every_required_domain_category() -> None:
    report = build_report()

    assert report.public_status == "block"
    assert report.category_count == d("7.000000")
    assert report.observed_category_count == d("0.000000")
    assert report.missing_category_count == d("7.000000")
    assert report.rows and len(report.rows) == 7
    assert {row.public_status for row in report.rows} == {"block"}
    assert {row.reason_codes for row in report.rows} == {
        ("research_team_domain_memory_staleness_missing_domain_memory",),
    }
    assert report.reason_codes == (
        "research_team_domain_memory_staleness_report_no_inputs",
        "research_team_domain_memory_staleness_report_block_present",
        "research_team_domain_memory_staleness_report_missing_domain_memory_present",
    )


@pytest.mark.parametrize(
    ("factory", "message"),
    (
        (
            lambda: observation(memory_coverage_ratio=0.8),
            "memory_coverage_ratio must be exactly Decimal",
        ),
        (
            lambda: observation(calibration_score=_DecimalSubclass("0.800000")),
            "calibration_score must be exactly Decimal",
        ),
        (
            lambda: observation(recent_outcome_feedback_count=2),
            "recent_outcome_feedback_count must be exactly Decimal",
        ),
        (
            lambda: config(min_recent_outcome_feedback_count=d("2.5")),
            "min_recent_outcome_feedback_count must be an integral Decimal",
        ),
        (
            lambda: build_report(generated_at=datetime(2026, 7, 8, 12, 0)),
            "generated_at must be timezone-aware",
        ),
        (
            lambda: build_report(
                observation(memory_updated_at=GENERATED_AT + timedelta(seconds=1)),
            ),
            "memory_updated_at must not be after generated_at",
        ),
        (
            lambda: build_report(
                observation(
                    last_outcome_feedback_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
            "last_outcome_feedback_at must not be after generated_at",
        ),
    ),
)
def test_decimal_and_type_validation_rejects_public_numeric_shortcuts(
    factory: Any,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        factory()


def test_frozen_dataclasses_and_hard_flags_are_enforced() -> None:
    module = api()
    cfg = config()
    item = observation()
    report = build_report(item)
    row = report.rows[-1]

    for value in (cfg, item, row, report):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        assert_public_numeric_values_are_decimal(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.ResearchTeamDomainMemoryStalenessConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(item, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="domain_category must be a public category"):
        observation(domain_category=_StringSubclass("politics"))
    with pytest.raises(ValueError, match="memory_updated_at must be a datetime"):
        observation(
            memory_updated_at=_DatetimeSubclass(2026, 7, 1, 12, 0, tzinfo=UTC),
        )


def test_payload_and_digest_are_deterministic_decimal_stringed_and_consistent() -> None:
    module = api()
    left = observation(domain_category="politics", team_key="policy-team")
    right = observation(
        domain_category="crypto",
        team_key="onchain-team",
        memory_updated_at=GENERATED_AT - timedelta(days=120),
        last_outcome_feedback_at=GENERATED_AT - timedelta(days=20),
        memory_coverage_ratio=d("0.600000"),
        calibration_score=d("0.650000"),
        settled_outcome_count=d("12.000000"),
        recent_outcome_feedback_count=d("2.000000"),
    )

    report_a = build_report(right, left)
    report_b = build_report(left, right)
    payload = module.research_team_domain_memory_staleness_report_payload(report_a)
    digest = module.research_team_domain_memory_staleness_report_digest(report_a)

    assert payload == module.research_team_domain_memory_staleness_report_payload(report_b)
    assert report_a.validation_digest == report_b.validation_digest
    assert payload["category_count"] == "7.000000"
    assert payload["rows"][-1]["domain_category"] == "politics"
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["validation_digest"] == report_a.validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert digest == module.research_team_domain_memory_staleness_report_digest(payload)
    assert digest["validation_digest"] == payload["validation_digest"]
    assert_no_float_values(payload)
    assert not any(type(value) is int for value in walk(payload))
    assert not any(isinstance(value, Decimal) for value in walk(payload))
    json.dumps(payload, allow_nan=False, sort_keys=True)

    statuses = {report_a.public_status}
    statuses.update(row.public_status for row in report_a.rows)
    assert statuses <= {"pass", "watch", "block"}

    tampered = dict(payload)
    tampered["public_status"] = "trade"
    with pytest.raises(ValueError, match="public_status must be pass, watch, or block"):
        module.research_team_domain_memory_staleness_report_payload(tampered)

    tampered_digest = dict(payload)
    tampered_digest["validation_digest"] = "sha256:" + ("0" * 64)
    with pytest.raises(ValueError, match="validation_digest must match report contents"):
        module.research_team_domain_memory_staleness_report_payload(tampered_digest)


def test_fractional_memory_age_seconds_remain_decimal_report_numerics() -> None:
    generated_at = datetime(2026, 7, 8, 12, 0, 0, 500000, tzinfo=UTC)
    report = build_report(
        observation(memory_updated_at=generated_at - timedelta(seconds=1, microseconds=250000)),
        generated_at=generated_at,
    )

    rows = {row.domain_category: row for row in report.rows}
    assert rows["politics"].oldest_memory_age_seconds == d("1.250000")
    assert report.max_oldest_memory_age_seconds == d("1.250000")
    assert report.payload["max_oldest_memory_age_seconds"] == "1.250000"


def test_payload_validation_enforces_row_flags_and_row_digests() -> None:
    module = api()
    report = build_report(observation())

    row_flag_payload = dict(report.payload)
    row_flag_payload["rows"] = [dict(row_flag_payload["rows"][0]), *row_flag_payload["rows"][1:]]
    row_flag_payload["rows"][0]["report_only"] = False
    with pytest.raises(ValueError, match="report_only must be True"):
        module.research_team_domain_memory_staleness_report_payload(row_flag_payload)

    row_digest_payload = dict(report.payload)
    row_digest_payload["rows"] = [
        dict(row_digest_payload["rows"][0]),
        *row_digest_payload["rows"][1:],
    ]
    row_digest_payload["rows"][0]["validation_digest"] = "sha256:" + ("0" * 64)
    with pytest.raises(ValueError, match="validation_digest must match report contents"):
        module.research_team_domain_memory_staleness_report_payload(row_digest_payload)


def test_public_payload_rejects_sensitive_surfaces_and_module_is_report_only() -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public payload"):
        observation(domain_category="market-politics")
    with pytest.raises(ValueError, match="unsafe public payload"):
        observation(team_key="wallet-team")

    report = build_report(observation())
    payload = dict(report.payload)
    payload["market_id"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_team_domain_memory_staleness_report_payload(payload)

    row_payload = dict(report.payload)
    row_payload["rows"] = [dict(row_payload["rows"][0])]
    row_payload["rows"][0]["source_text"] = "hidden note"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_team_domain_memory_staleness_report_payload(row_payload)

    assert_public_payload_has_no_forbidden_surface(report.payload)
    public_json = json.dumps(report.payload, sort_keys=True).lower()
    assert "policy-team" not in public_json
    assert "wallet" not in public_json
    assert "market" not in public_json
    assert "source" not in public_json

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "db",
        "http",
        "network",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sql",
        "subprocess",
        "urllib",
        "web3",
        "websocket",
    )
    forbidden_call_fragments = (
        "connect",
        "delete",
        "execute",
        "insert",
        "open",
        "patch",
        "post",
        "put",
        "request",
        "send",
        "sign",
        "submit",
        "trade",
        "write",
    )
    forbidden_attribute_fragments = (
        "private_key",
        "place_order",
        "submit_order",
        "wallet",
    )

    assert float_constants == []
    assert not any(
        fragment in imported.lower()
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(
        fragment in call.lower()
        for call in call_names
        for fragment in forbidden_call_fragments
    )
    assert not any(
        fragment in attribute.lower()
        for attribute in attribute_names
        for fragment in forbidden_attribute_fragments
    )
