from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_domain_decision_memory_decay_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_domain_decision_memory_decay_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            "research-team-domain-decision-memory-decay-report-test"
        ),
        "watch_memory_decay_after_seconds": d("5184000.000000"),
        "block_memory_decay_after_seconds": d("10368000.000000"),
        "stale_review_after_seconds": d("3888000.000000"),
        "max_watch_unresolved_decisions": d("3.000000"),
        "max_block_unresolved_decisions": d("8.000000"),
        "min_pass_memory_reuse_ratio": d("0.650000"),
        "min_watch_memory_reuse_ratio": d("0.400000"),
        "min_pass_calibration_score": d("0.700000"),
        "min_watch_calibration_score": d("0.500000"),
        "min_pass_decision_hit_rate": d("0.650000"),
        "min_watch_decision_hit_rate": d("0.450000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainDecisionMemoryDecayConfig(**values)


def observation(**overrides: object):
    module = api()
    values = {
        "domain_category": "politics",
        "team_key": "policy-team",
        "decision_memory_updated_at": GENERATED_AT - timedelta(days=20),
        "latest_decision_review_at": GENERATED_AT - timedelta(days=10),
        "resolved_decision_count": d("10.000000"),
        "unresolved_decision_count": d("1.000000"),
        "decision_hit_rate": d("0.760000"),
        "decision_calibration_score": d("0.820000"),
        "memory_reuse_ratio": d("0.800000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainDecisionMemoryDecayObservation(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_domain_decision_memory_decay_report(
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

    assert (
        module.DEFAULT_RESEARCH_TEAM_DOMAIN_DECISION_MEMORY_DECAY_REPORT_CONFIG_VERSION
        == "research-team-domain-decision-memory-decay-report-v0"
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
        "DEFAULT_RESEARCH_TEAM_DOMAIN_DECISION_MEMORY_DECAY_REPORT_CONFIG_VERSION",
        "PUBLIC_DOMAIN_CATEGORIES",
        "PUBLIC_STATUSES",
        "ResearchTeamDomainDecisionMemoryDecayConfig",
        "ResearchTeamDomainDecisionMemoryDecayObservation",
        "ResearchTeamDomainDecisionMemoryDecayRow",
        "ResearchTeamDomainDecisionMemoryDecayReport",
        "build_research_team_domain_decision_memory_decay_report",
        "research_team_domain_decision_memory_decay_report_payload",
        "research_team_domain_decision_memory_decay_report_digest",
    )

    field_defaults = {
        field.name: field.default
        for field in fields(module.ResearchTeamDomainDecisionMemoryDecayConfig)
    }
    assert field_defaults["paper_only"] is True
    assert field_defaults["report_only"] is True
    assert field_defaults["readonly"] is True


def test_builds_pass_watch_block_and_missing_domain_rows() -> None:
    report = build_report(
        observation(domain_category="politics", team_key="policy-team"),
        observation(
            domain_category="politics",
            team_key="legal-team",
            resolved_decision_count=d("12.000000"),
            unresolved_decision_count=d("1.000000"),
            decision_hit_rate=d("0.800000"),
            decision_calibration_score=d("0.880000"),
            memory_reuse_ratio=d("0.820000"),
        ),
        observation(
            domain_category="crypto",
            team_key="onchain-team",
            decision_memory_updated_at=GENERATED_AT - timedelta(days=75),
            latest_decision_review_at=GENERATED_AT - timedelta(days=50),
            resolved_decision_count=d("8.000000"),
            unresolved_decision_count=d("4.000000"),
            decision_hit_rate=d("0.600000"),
            decision_calibration_score=d("0.650000"),
            memory_reuse_ratio=d("0.550000"),
        ),
        observation(
            domain_category="equities",
            team_key="index-team",
            decision_memory_updated_at=GENERATED_AT - timedelta(days=150),
            latest_decision_review_at=None,
            resolved_decision_count=d("5.000000"),
            unresolved_decision_count=d("9.000000"),
            decision_hit_rate=d("0.300000"),
            decision_calibration_score=d("0.400000"),
            memory_reuse_ratio=d("0.200000"),
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
    assert report.decayed_category_count == d("2.000000")
    assert report.stale_review_category_count == d("2.000000")
    assert report.unresolved_category_count == d("2.000000")
    assert report.low_reuse_category_count == d("2.000000")
    assert report.low_calibration_category_count == d("2.000000")
    assert report.average_decision_hit_rate == d("0.560000")
    assert report.average_decision_calibration_score == d("0.633333")
    assert report.average_memory_reuse_ratio == d("0.520000")
    assert report.max_oldest_decision_memory_age_seconds == d("12960000.000000")
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
    assert rows["politics"].resolved_decision_count == d("22.000000")
    assert rows["politics"].unresolved_decision_count == d("2.000000")
    assert rows["politics"].average_decision_hit_rate == d("0.780000")
    assert rows["politics"].average_decision_calibration_score == d("0.850000")
    assert rows["politics"].average_memory_reuse_ratio == d("0.810000")
    assert rows["politics"].reason_codes == (
        "research_team_domain_decision_memory_decay_healthy_memory",
    )

    assert rows["crypto"].public_status == "watch"
    assert rows["crypto"].oldest_decision_memory_age_seconds == d("6480000.000000")
    assert rows["crypto"].reason_codes == (
        "research_team_domain_decision_memory_decay_watch_memory_decay",
        "research_team_domain_decision_memory_decay_stale_review",
        "research_team_domain_decision_memory_decay_high_unresolved_decisions",
        "research_team_domain_decision_memory_decay_low_reuse",
        "research_team_domain_decision_memory_decay_low_calibration",
    )

    assert rows["equities"].public_status == "block"
    assert rows["equities"].newest_decision_review_age_seconds is None
    assert rows["equities"].reason_codes == (
        "research_team_domain_decision_memory_decay_block_memory_decay",
        "research_team_domain_decision_memory_decay_stale_review",
        "research_team_domain_decision_memory_decay_block_unresolved_decisions",
        "research_team_domain_decision_memory_decay_block_low_reuse",
        "research_team_domain_decision_memory_decay_block_low_calibration",
    )

    assert rows["basketball"].public_status == "block"
    assert rows["basketball"].team_count == d("0.000000")
    assert rows["basketball"].reason_codes == (
        "research_team_domain_decision_memory_decay_missing_memory",
    )
    assert rows["basketball"].validation_digest.startswith("sha256:")

    assert report.reason_codes == (
        "research_team_domain_decision_memory_decay_report_block_present",
        "research_team_domain_decision_memory_decay_report_watch_present",
        "research_team_domain_decision_memory_decay_report_missing_memory_present",
        "research_team_domain_decision_memory_decay_report_memory_decay_present",
        "research_team_domain_decision_memory_decay_report_stale_review_present",
        "research_team_domain_decision_memory_decay_report_unresolved_present",
        "research_team_domain_decision_memory_decay_report_low_reuse_present",
        "research_team_domain_decision_memory_decay_report_low_calibration_present",
        "research_team_domain_decision_memory_decay_report_healthy_memory_present",
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
        ("research_team_domain_decision_memory_decay_missing_memory",),
    }
    assert report.reason_codes == (
        "research_team_domain_decision_memory_decay_report_no_inputs",
        "research_team_domain_decision_memory_decay_report_block_present",
        "research_team_domain_decision_memory_decay_report_missing_memory_present",
    )


@pytest.mark.parametrize(
    ("factory", "message"),
    (
        (
            lambda: observation(memory_reuse_ratio=0.8),
            "memory_reuse_ratio must be exactly Decimal",
        ),
        (
            lambda: observation(decision_calibration_score=_DecimalSubclass("0.800000")),
            "decision_calibration_score must be exactly Decimal",
        ),
        (
            lambda: observation(unresolved_decision_count=2),
            "unresolved_decision_count must be exactly Decimal",
        ),
        (
            lambda: config(max_watch_unresolved_decisions=d("2.5")),
            "max_watch_unresolved_decisions must be an integral Decimal",
        ),
        (
            lambda: build_report(generated_at=datetime(2026, 7, 9, 12, 0)),
            "generated_at must be timezone-aware",
        ),
        (
            lambda: observation(
                decision_memory_updated_at=_DatetimeSubclass(
                    2026,
                    7,
                    1,
                    12,
                    0,
                    tzinfo=UTC,
                ),
            ),
            "decision_memory_updated_at must be a datetime",
        ),
        (
            lambda: observation(
                latest_decision_review_at=datetime(
                    2026,
                    7,
                    1,
                    12,
                    0,
                    tzinfo=_NoneOffsetTimezone(),
                ),
            ),
            "latest_decision_review_at must have a valid UTC offset",
        ),
        (
            lambda: build_report(
                observation(
                    decision_memory_updated_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
            "decision_memory_updated_at must not be after generated_at",
        ),
        (
            lambda: build_report(
                observation(
                    latest_decision_review_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
            "latest_decision_review_at must not be after generated_at",
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
        module.ResearchTeamDomainDecisionMemoryDecayConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(item, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="domain_category must be exactly str"):
        observation(domain_category=_StringSubclass("politics"))
    with pytest.raises(ValueError, match="watch_memory_decay_after_seconds"):
        config(block_memory_decay_after_seconds=d("100.000000"))


def test_payload_and_digest_are_deterministic_decimal_stringed_and_consistent() -> None:
    module = api()
    left = observation(domain_category="politics", team_key="policy-team")
    right = observation(
        domain_category="crypto",
        team_key="onchain-team",
        decision_memory_updated_at=GENERATED_AT - timedelta(days=75),
        latest_decision_review_at=GENERATED_AT - timedelta(days=50),
        resolved_decision_count=d("8.000000"),
        unresolved_decision_count=d("4.000000"),
        decision_hit_rate=d("0.600000"),
        decision_calibration_score=d("0.650000"),
        memory_reuse_ratio=d("0.550000"),
    )

    report_a = build_report(right, left)
    report_b = build_report(left, right)
    payload = module.research_team_domain_decision_memory_decay_report_payload(report_a)
    digest = module.research_team_domain_decision_memory_decay_report_digest(report_a)

    assert payload == module.research_team_domain_decision_memory_decay_report_payload(report_b)
    assert report_a.validation_digest == report_b.validation_digest
    assert payload["category_count"] == "7.000000"
    assert payload["rows"][-1]["domain_category"] == "politics"
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["validation_digest"] == report_a.validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert digest == module.research_team_domain_decision_memory_decay_report_digest(payload)
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
        module.research_team_domain_decision_memory_decay_report_payload(tampered)

    tampered_digest = dict(payload)
    tampered_digest["validation_digest"] = "sha256:" + ("0" * 64)
    with pytest.raises(ValueError, match="validation_digest must match report contents"):
        module.research_team_domain_decision_memory_decay_report_payload(tampered_digest)


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
        module.research_team_domain_decision_memory_decay_report_payload(payload)

    row_payload = dict(report.payload)
    row_payload["rows"] = [dict(row_payload["rows"][0])]
    row_payload["rows"][0]["source_text"] = "hidden note"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_team_domain_decision_memory_decay_report_payload(row_payload)

    assert_public_payload_has_no_forbidden_surface(report.payload)
    public_json = json.dumps(report.payload, sort_keys=True).lower()
    assert "policy-team" not in public_json
    assert "wallet" not in public_json
    assert "market" not in public_json
    assert "source" not in public_json
    assert "order" not in public_json
    assert "trade" not in public_json

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
