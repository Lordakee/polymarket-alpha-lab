from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_cross_domain_memory_quorum_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _MissingOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_cross_domain_memory_quorum_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "pass_quorum_score_threshold": d("0.750000"),
        "block_quorum_score_threshold": d("0.450000"),
        "min_pass_independent_domain_memory_count": d("3"),
        "min_watch_independent_domain_memory_count": d("2"),
        "stale_memory_age_seconds": d("86400.000000"),
        "stale_calibration_age_seconds": d("604800.000000"),
        "pass_component_score_threshold": d("0.750000"),
        "block_component_score_threshold": d("0.350000"),
        "pass_contradiction_pressure_score": d("0.250000"),
        "block_contradiction_pressure_score": d("0.700000"),
        "pass_evidence_reuse_quality_score": d("0.700000"),
        "block_evidence_reuse_quality_score": d("0.400000"),
        "pass_open_review_load_pressure_score": d("0.300000"),
        "block_open_review_load_pressure_score": d("0.800000"),
        "max_open_review_count": d("10"),
        "independent_domain_memory_weight": d("0.250000"),
        "memory_freshness_weight": d("0.150000"),
        "calibration_recency_weight": d("0.150000"),
        "contradiction_pressure_weight": d("0.200000"),
        "evidence_reuse_quality_weight": d("0.150000"),
        "open_review_load_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchTeamCrossDomainMemoryQuorumConfig(**values)


def observation(**overrides: object) -> Any:
    module = api()
    values = {
        "quorum_key": "quorum_alpha",
        "domain_key": "macro_rates",
        "captured_at": datetime(2026, 7, 8, 11, 0, tzinfo=UTC),
        "calibrated_at": datetime(2026, 7, 8, 0, 0, tzinfo=UTC),
        "contradiction_pressure_score": d("0.100000"),
        "evidence_reuse_quality_score": d("0.900000"),
        "open_review_count": d("1"),
    }
    values.update(overrides)
    return module.ResearchTeamCrossDomainMemoryQuorumObservation(**values)


def build_report(
    *items: object,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_team_cross_domain_memory_quorum_report(
        items,
        generated_at=generated_at,
        config=cfg,
    )


def assert_no_public_float_or_int(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_float_or_int(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_float_or_int(item)


def assert_no_decimal_or_datetime(value: Any) -> None:
    if isinstance(value, (Decimal, datetime)):
        raise AssertionError(f"unexpected raw public value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_decimal_or_datetime(item)
    if isinstance(value, list):
        for item in value:
            assert_no_decimal_or_datetime(item)


def payload_keys(value: Any) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            keys.append(str(key))
            keys.extend(payload_keys(item))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for item in value:
            keys.extend(payload_keys(item))
        return tuple(keys)
    return ()


def test_scores_pass_watch_and_block_memory_quorum_rows() -> None:
    module = api()
    result = build_report(
        observation(quorum_key="quorum_alpha", domain_key="macro_rates"),
        observation(quorum_key="quorum_alpha", domain_key="crypto_research"),
        observation(quorum_key="quorum_alpha", domain_key="weather_research"),
        observation(
            quorum_key="quorum_beta",
            domain_key="macro_rates",
            captured_at=datetime(2026, 7, 8, 0, 0, tzinfo=UTC),
            calibrated_at=datetime(2026, 7, 6, 12, 0, tzinfo=UTC),
            contradiction_pressure_score=d("0.350000"),
            evidence_reuse_quality_score=d("0.650000"),
            open_review_count=d("2"),
        ),
        observation(
            quorum_key="quorum_beta",
            domain_key="crypto_research",
            captured_at=datetime(2026, 7, 8, 0, 0, tzinfo=UTC),
            calibrated_at=datetime(2026, 7, 6, 12, 0, tzinfo=UTC),
            contradiction_pressure_score=d("0.350000"),
            evidence_reuse_quality_score=d("0.650000"),
            open_review_count=d("2"),
        ),
        observation(
            quorum_key="quorum_gamma",
            domain_key="macro_rates",
            captured_at=datetime(2026, 7, 6, 12, 0, tzinfo=UTC),
            calibrated_at=datetime(2026, 6, 28, 12, 0, tzinfo=UTC),
            contradiction_pressure_score=d("0.900000"),
            evidence_reuse_quality_score=d("0.200000"),
            open_review_count=d("12"),
        ),
    )

    assert is_dataclass(result)
    assert module.PUBLIC_STATUSES == ("pass", "watch", "block")
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "research-team-cross-domain-memory-quorum-report-v0"
    assert result.report_status == "block"
    assert result.quorum_count == d("3")
    assert result.observation_count == d("6")
    assert result.domain_memory_count == d("6")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.average_quorum_score == d("0.562560")
    assert result.min_quorum_score == d("0.133333")
    assert result.max_open_review_load_pressure_score == d("1.000000")
    assert result.reason_codes == (
        "cross_domain_memory_quorum_report_block",
        "insufficient_independent_domain_memory_block",
        "memory_freshness_block",
        "calibration_recency_block",
        "contradiction_pressure_block",
        "evidence_reuse_quality_block",
        "open_review_load_block",
        "insufficient_independent_domain_memory_watch",
        "memory_freshness_watch",
        "calibration_recency_watch",
        "contradiction_pressure_watch",
        "evidence_reuse_quality_watch",
        "open_review_load_watch",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.public_digest) == len("sha256:") + 64

    block_row, watch_row, pass_row = result.rows
    assert block_row.quorum_key == "quorum_gamma"
    assert block_row.status == "block"
    assert block_row.independent_domain_memory_count == d("1")
    assert block_row.independent_domain_memory_score == d("0.333333")
    assert block_row.max_memory_age_seconds == d("172800.000000")
    assert block_row.memory_freshness_score == d("0.000000")
    assert block_row.max_calibration_age_seconds == d("864000.000000")
    assert block_row.calibration_recency_score == d("0.000000")
    assert block_row.average_contradiction_pressure_score == d("0.900000")
    assert block_row.average_evidence_reuse_quality_score == d("0.200000")
    assert block_row.total_open_review_count == d("12")
    assert block_row.open_review_load_pressure_score == d("1.000000")
    assert block_row.quorum_score == d("0.133333")
    assert block_row.reason_codes == (
        "cross_domain_memory_quorum_block",
        "insufficient_independent_domain_memory_block",
        "memory_freshness_block",
        "calibration_recency_block",
        "contradiction_pressure_block",
        "evidence_reuse_quality_block",
        "open_review_load_block",
    )

    assert watch_row.quorum_key == "quorum_beta"
    assert watch_row.status == "watch"
    assert watch_row.independent_domain_memory_count == d("2")
    assert watch_row.memory_freshness_score == d("0.500000")
    assert watch_row.calibration_recency_score == d("0.714286")
    assert watch_row.quorum_score == d("0.636310")

    assert pass_row.quorum_key == "quorum_alpha"
    assert pass_row.status == "pass"
    assert pass_row.independent_domain_memory_count == d("3")
    assert pass_row.quorum_score == d("0.918036")
    assert pass_row.reason_codes == ("cross_domain_memory_quorum_pass",)

    for value in (result, *result.rows):
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item.name.endswith(("_count", "_score", "_seconds")):
                assert type(item_value) is Decimal


def test_memory_freshness_uses_generated_at_and_rejects_future_inputs() -> None:
    stale = build_report(
        observation(
            captured_at=GENERATED_AT - timedelta(seconds=86400),
            calibrated_at=GENERATED_AT - timedelta(seconds=604800),
        ),
    )
    row = stale.rows[0]

    assert row.max_memory_age_seconds == d("86400.000000")
    assert row.memory_freshness_score == d("0.000000")
    assert row.calibration_recency_score == d("0.000000")
    assert row.status == "block"
    assert "memory_freshness_block" in row.reason_codes
    assert "calibration_recency_block" in row.reason_codes

    with pytest.raises(ValueError, match="captured_at"):
        build_report(observation(captured_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="calibrated_at"):
        build_report(observation(calibrated_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(observation(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="captured_at"):
        observation(captured_at=datetime(2026, 7, 8, 11, 0))
    with pytest.raises(ValueError, match="captured_at"):
        observation(captured_at=_DatetimeSubclass(2026, 7, 8, 11, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="captured_at"):
        observation(captured_at=datetime(2026, 7, 8, 11, 0, tzinfo=_MissingOffsetTz()))


def test_public_payload_is_deterministic_json_safe_and_digest_checked() -> None:
    module = api()
    first = build_report(
        observation(
            quorum_key="quorum_delta",
            domain_key="crypto_research",
            captured_at=datetime(2026, 7, 8, 4, 30, tzinfo=timezone(timedelta(hours=-7))),
            calibrated_at=datetime(2026, 7, 7, 17, 0, tzinfo=timezone(timedelta(hours=-7))),
            contradiction_pressure_score=d("0.200000"),
            evidence_reuse_quality_score=d("0.800000"),
            open_review_count=d("1"),
        ),
        observation(
            quorum_key="quorum_delta",
            domain_key="macro_rates",
            captured_at=datetime(2026, 7, 8, 11, 30, tzinfo=UTC),
            calibrated_at=datetime(2026, 7, 8, 1, 0, tzinfo=UTC),
            contradiction_pressure_score=d("0.100000"),
            evidence_reuse_quality_score=d("0.900000"),
            open_review_count=d("1"),
        ),
        generated_at=datetime(2026, 7, 8, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    second = build_report(
        observation(
            quorum_key="quorum_delta",
            domain_key="macro_rates",
            captured_at=datetime(2026, 7, 8, 11, 30, tzinfo=UTC),
            calibrated_at=datetime(2026, 7, 8, 1, 0, tzinfo=UTC),
            contradiction_pressure_score=d("0.100000"),
            evidence_reuse_quality_score=d("0.900000"),
            open_review_count=d("1"),
        ),
        observation(
            quorum_key="quorum_delta",
            domain_key="crypto_research",
            captured_at=datetime(2026, 7, 8, 11, 30, tzinfo=UTC),
            calibrated_at=datetime(2026, 7, 8, 0, 0, tzinfo=UTC),
            contradiction_pressure_score=d("0.200000"),
            evidence_reuse_quality_score=d("0.800000"),
            open_review_count=d("1"),
        ),
    )

    payload = module.research_team_cross_domain_memory_quorum_public_payload(first)
    repeat_payload = module.research_team_cross_domain_memory_quorum_public_payload(second)

    assert first.public_digest == second.public_digest
    assert payload == repeat_payload
    assert payload == first.public_payload
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["quorum_count"] == "1"
    assert payload["rows"][0]["latest_memory_captured_at"] == "2026-07-08T11:30:00+00:00"
    assert payload["rows"][0]["quorum_score"] == "0.830327"
    assert payload["public_digest"] == first.public_digest
    assert_no_public_float_or_int(payload)
    assert_no_decimal_or_datetime(payload)
    json.dumps(payload, sort_keys=True)

    forbidden_fragments = (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "source",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
    )
    encoded = json.dumps(payload, sort_keys=True).lower()
    assert not any(
        fragment in key.lower()
        for key in payload_keys(payload)
        for fragment in forbidden_fragments
    )
    assert not any(fragment in encoded for fragment in forbidden_fragments)

    tampered = dict(payload)
    tampered["pass_count"] = "2"
    with pytest.raises(ValueError, match="public_digest"):
        module.research_team_cross_domain_memory_quorum_public_payload(tampered)

    with pytest.raises(ValueError, match="public_digest|pass_count"):
        replace(first, pass_count=d("2"))


def test_rejects_leaky_identifiers_numerics_flags_and_mutation() -> None:
    module = api()
    result = build_report(observation())
    row = result.rows[0]
    payload = module.research_team_cross_domain_memory_quorum_public_payload(result)

    with pytest.raises(FrozenInstanceError):
        result.report_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="Decimal"):
        observation(contradiction_pressure_score=1)
    with pytest.raises(ValueError, match="Decimal"):
        observation(evidence_reuse_quality_score=0.5)
    with pytest.raises(ValueError, match="Decimal"):
        observation(open_review_count=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="quorum_key"):
        observation(quorum_key="market_slug_alpha")
    with pytest.raises(ValueError, match="domain_key"):
        observation(domain_key="source_url_alpha")
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_report(observation(), cfg=object())
    with pytest.raises(ValueError, match="status"):
        replace(row, status="blocked")
    with pytest.raises(ValueError, match="public_digest"):
        replace(result, public_digest="sha256:" + "0" * 64)

    leaky_key = dict(payload)
    leaky_key["market_id"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_team_cross_domain_memory_quorum_public_payload(leaky_key)

    leaky_value = dict(payload)
    leaky_value["note"] = "https://example.invalid/redacted"
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_team_cross_domain_memory_quorum_public_payload(leaky_value)

    numeric = dict(payload)
    numeric["quorum_count"] = 1
    with pytest.raises(ValueError, match="numeric"):
        module.research_team_cross_domain_memory_quorum_public_payload(numeric)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.research_team_cross_domain_memory_quorum_public_payload(downgraded)


def test_custom_config_validation_and_thresholds() -> None:
    module = api()
    custom = config(
        pass_quorum_score_threshold=d("0.600000"),
        block_quorum_score_threshold=d("0.300000"),
        min_pass_independent_domain_memory_count=d("2"),
        min_watch_independent_domain_memory_count=d("1"),
    )
    result = build_report(
        observation(quorum_key="quorum_custom", domain_key="macro_rates"),
        observation(quorum_key="quorum_custom", domain_key="crypto_research"),
        cfg=custom,
    )

    assert result.report_status == "pass"
    assert result.rows[0].status == "pass"
    assert result.rows[0].independent_domain_memory_score == d("1.000000")

    with pytest.raises(ValueError, match="supported config version"):
        config(config_version="research-team-cross-domain-memory-quorum-report-v9")
    with pytest.raises(ValueError, match="must exceed"):
        config(pass_quorum_score_threshold=d("0.200000"), block_quorum_score_threshold=d("0.200000"))
    with pytest.raises(ValueError, match="must not exceed"):
        config(
            min_pass_independent_domain_memory_count=d("1"),
            min_watch_independent_domain_memory_count=d("2"),
        )
    with pytest.raises(ValueError, match="sum"):
        config(independent_domain_memory_weight=d("0.240000"))
    with pytest.raises(ValueError, match="Decimal"):
        config(max_open_review_count=10)
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)

    with pytest.raises(TypeError):
        class BadConfig(module.ResearchTeamCrossDomainMemoryQuorumConfig):
            pass


def test_module_is_report_only_without_external_write_or_execution_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
    banned_import_roots = {
        "http",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "urllib",
        "web3",
    }
    banned_call_names = {
        "buy",
        "connect",
        "delete",
        "execute",
        "executemany",
        "get",
        "open",
        "order",
        "patch",
        "post",
        "put",
        "request",
        "sell",
        "send",
        "submit",
        "trade",
        "write",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in banned_import_roots
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in banned_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in banned_call_names
