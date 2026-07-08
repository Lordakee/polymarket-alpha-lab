from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt):  # type: ignore[no-untyped-def]
        return None

    def dst(self, dt):  # type: ignore[no-untyped-def]
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_source_claim_timeliness_score_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def ago(seconds: int) -> datetime:
    return GENERATED_AT - timedelta(seconds=seconds)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-source-claim-timeliness-score-v0",
        "watch_claim_age_seconds": d("21600.000000"),
        "block_claim_age_seconds": d("86400.000000"),
        "watch_update_latency_seconds": d("7200.000000"),
        "block_update_latency_seconds": d("21600.000000"),
        "watch_corroboration_delay_seconds": d("14400.000000"),
        "block_corroboration_delay_seconds": d("43200.000000"),
        "watch_stale_contradiction_pressure": d("0.250000"),
        "block_stale_contradiction_pressure": d("0.750000"),
        "watch_manual_escalation_urgency": d("0.500000"),
        "block_manual_escalation_urgency": d("1.000000"),
    }
    values.update(overrides)
    return module.ResearchSourceClaimTimelinessScoreConfig(**values)


def observation(**overrides: object):
    module = api()
    values = {
        "source_class": "official",
        "claim_observed_at": ago(3600),
        "source_updated_at": ago(1800),
        "corroborated_at": ago(2700),
        "stale_contradiction_count": d("0"),
        "manual_escalation_signal": False,
    }
    values.update(overrides)
    return module.ResearchSourceClaimTimelinessObservation(**values)


def report(*rows, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_source_claim_timeliness_score_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_float(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float(item)
    else:
        assert type(value) is not float


def test_report_aggregates_source_claim_timeliness_by_source_class() -> None:
    score_report = report(
        observation(source_class="official"),
        observation(
            source_class="newswire",
            claim_observed_at=ago(28800),
            source_updated_at=ago(10800),
            corroborated_at=ago(10800),
            stale_contradiction_count=d("1"),
            manual_escalation_signal=True,
        ),
        observation(
            source_class="newswire",
            claim_observed_at=ago(7200),
            source_updated_at=ago(3600),
            corroborated_at=ago(3600),
            stale_contradiction_count=d("0"),
            manual_escalation_signal=False,
        ),
        observation(
            source_class="social",
            claim_observed_at=ago(90000),
            source_updated_at=ago(30000),
            corroborated_at=None,
            stale_contradiction_count=d("2"),
            manual_escalation_signal=True,
        ),
    )

    assert score_report.generated_at == GENERATED_AT
    assert score_report.source_class_count == d("3")
    assert score_report.claim_count == d("4")
    assert score_report.pass_count == d("1")
    assert score_report.watch_count == d("1")
    assert score_report.block_count == d("1")
    assert score_report.average_claim_age_seconds == d("32400.000000")
    assert score_report.max_update_latency_seconds == d("30000.000000")
    assert score_report.max_corroboration_delay_seconds == d("90000.000000")
    assert score_report.max_stale_contradiction_pressure == d("1.000000")
    assert score_report.max_manual_escalation_urgency == d("1.000000")
    assert score_report.status == "block"
    assert score_report.paper_only is True
    assert score_report.report_only is True
    assert score_report.readonly is True

    rows = {row.source_class: row for row in score_report.rows}
    assert tuple(sorted(rows)) == ("newswire", "official", "social")

    assert rows["official"].status == "pass"
    assert rows["official"].reason_codes == ("source_class_timeliness_pass",)
    assert rows["official"].average_claim_age_seconds == d("3600.000000")
    assert rows["official"].average_update_latency_seconds == d("1800.000000")
    assert rows["official"].average_corroboration_delay_seconds == d("900.000000")

    assert rows["newswire"].status == "watch"
    assert rows["newswire"].claim_count == d("2")
    assert rows["newswire"].average_claim_age_seconds == d("18000.000000")
    assert rows["newswire"].max_claim_age_seconds == d("28800.000000")
    assert rows["newswire"].average_update_latency_seconds == d("7200.000000")
    assert rows["newswire"].max_update_latency_seconds == d("10800.000000")
    assert rows["newswire"].average_corroboration_delay_seconds == d("10800.000000")
    assert rows["newswire"].max_corroboration_delay_seconds == d("18000.000000")
    assert rows["newswire"].stale_contradiction_pressure == d("0.500000")
    assert rows["newswire"].manual_escalation_urgency == d("0.500000")
    assert rows["newswire"].reason_codes == (
        "claim_age_watch",
        "update_latency_watch",
        "corroboration_delay_watch",
        "stale_contradiction_pressure_watch",
        "manual_escalation_urgency_watch",
    )

    assert rows["social"].status == "block"
    assert rows["social"].claim_count == d("1")
    assert rows["social"].average_claim_age_seconds == d("90000.000000")
    assert rows["social"].average_corroboration_delay_seconds == d("90000.000000")
    assert rows["social"].stale_contradiction_pressure == d("1.000000")
    assert rows["social"].manual_escalation_urgency == d("1.000000")
    assert rows["social"].reason_codes == (
        "claim_age_block",
        "update_latency_block",
        "corroboration_delay_block",
        "stale_contradiction_pressure_block",
        "manual_escalation_urgency_block",
    )


def test_public_payload_is_deterministic_decimal_only_and_digest_validated() -> None:
    module = api()
    score_report = report(
        observation(source_class="newswire", manual_escalation_signal=True),
        generated_at=datetime(2026, 7, 8, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.research_source_claim_timeliness_score_report_payload(score_report)
    payload_text = repr(payload).lower()
    payload_without_digest = dict(payload)
    digest_value = payload_without_digest.pop("derived_validation_digest")
    canonical = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )

    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["claim_count"] == "1"
    assert payload["rows"][0]["source_class"] == "newswire"
    assert payload["rows"][0]["average_claim_age_seconds"] == "3600.000000"
    assert score_report.derived_validation_digest == digest_value
    assert sha256(canonical.encode("utf-8")).hexdigest() == digest_value
    assert "Decimal(" not in repr(payload)
    assert "datetime" not in payload_text
    assert "http" not in payload_text
    assert "raw" not in payload_text
    assert "market" not in payload_text
    assert "candidate" not in payload_text
    assert_no_float(payload)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(score_report, derived_validation_digest="0" * 64)


def test_report_validates_inputs_flags_statuses_and_frozen_outputs() -> None:
    module = api()
    score_report = report(observation())

    assert module.STATUSES == ("pass", "watch", "block")
    with pytest.raises(FrozenInstanceError):
        score_report.rows[0].status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="claim_observed_at must be a datetime"):
        observation(claim_observed_at=_DatetimeSubclass(2026, 7, 8, 11, tzinfo=UTC))

    with pytest.raises(ValueError, match="claim_observed_at must be timezone-aware"):
        observation(claim_observed_at=datetime(2026, 7, 8, 11, tzinfo=_NoneOffsetTimezone()))

    with pytest.raises(ValueError, match="stale_contradiction_count must be a Decimal"):
        observation(stale_contradiction_count=1)

    with pytest.raises(ValueError, match="stale_contradiction_count must be a Decimal"):
        observation(stale_contradiction_count=_DecimalSubclass("1"))

    with pytest.raises(ValueError, match="watch_claim_age_seconds must be finite"):
        config(watch_claim_age_seconds=Decimal("NaN"))

    with pytest.raises(ValueError, match="config_version"):
        config(config_version="research-source-claim-timeliness-score-v1")

    with pytest.raises(ValueError, match="source_class has unsafe public value"):
        observation(source_class="https://example.com/raw-item")

    with pytest.raises(ValueError, match="source_class has unsafe public value"):
        observation(source_class="candidate_alpha")

    with pytest.raises(ValueError, match="source_class has unsafe public value"):
        observation(source_class="market_alpha")

    for unsafe_source_class in (
        "slug_alpha",
        "question_alpha",
        "text_alpha",
        "dsn_alpha",
        "table_alpha",
        "token_alpha",
        "wallet_alpha",
        "order_alpha",
        "trade_alpha",
        "auth_alpha",
        "private_key_alpha",
        "secret_alpha",
    ):
        with pytest.raises(ValueError, match="source_class has unsafe public value"):
            observation(source_class=unsafe_source_class)

    with pytest.raises(ValueError, match="config must be readonly"):
        config(readonly=False)

    with pytest.raises(ValueError, match="observation must be paper_only"):
        observation(paper_only=False)

    with pytest.raises(ValueError, match="status"):
        replace(score_report.rows[0], status="blocked")

    with pytest.raises(ValueError, match="claim_count"):
        replace(score_report, claim_count=d("2"))


def test_report_rejects_temporal_inconsistency_and_empty_inputs() -> None:
    with pytest.raises(ValueError, match="observations must not be empty"):
        report()

    with pytest.raises(ValueError, match="claim_observed_at must not be after generated_at"):
        report(
            observation(
                claim_observed_at=GENERATED_AT + timedelta(seconds=1),
                source_updated_at=GENERATED_AT + timedelta(seconds=2),
                corroborated_at=None,
            ),
        )

    with pytest.raises(ValueError, match="source_updated_at must not be before claim_observed_at"):
        observation(
            claim_observed_at=ago(3600),
            source_updated_at=ago(7200),
        )

    with pytest.raises(ValueError, match="corroborated_at must not be before claim_observed_at"):
        observation(
            claim_observed_at=ago(3600),
            corroborated_at=ago(7200),
        )


def test_module_scope_has_no_forbidden_runtime_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_source_claim_timeliness_score_report.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_modules = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite3",
        "sqlite",
        "supabase",
    )
    forbidden_runtime_names = (
        "wallet",
        "signing",
        "private_key",
        "api_key",
        "auth",
        "token",
        "dsn",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "submit",
        "cancel",
        "replace_order",
        "create_order",
        "execute",
        "connect",
        "commit",
        "rollback",
        "cursor",
        "open",
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", maxsplit=1)[0] not in forbidden_modules
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", maxsplit=1)[0] not in forbidden_modules
        if isinstance(node, ast.Name):
            assert node.id.lower() not in forbidden_runtime_names
        if isinstance(node, ast.Attribute):
            assert node.attr.lower() not in forbidden_runtime_names
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id != "float"
                assert node.func.id.lower() not in forbidden_runtime_names
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr.lower() not in forbidden_runtime_names


def test_elapsed_time_uses_decimal_safe_datetime_arithmetic() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_source_claim_timeliness_score_report.py",
    ).read_text(encoding="utf-8")

    assert ".timestamp(" not in source
    assert ".total_seconds(" not in source
