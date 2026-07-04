from __future__ import annotations

import ast
import importlib
import json
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_recommendation_gate_reason_rollup_digest"
GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 4, 11, 30, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt):  # type: ignore[override]
        return None


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-recommendation-gate-reason-rollup-test-v0",
        "max_top_blockers": d("3"),
    }
    values.update(overrides)
    return module.StrategyRecommendationGateReasonRollupDigestConfig(**values)


def gate_row(candidate_id: str = "candidate-alpha", **overrides: object):
    module = api()
    values = {
        "candidate_id": candidate_id,
        "category_id": "macro.policy",
        "team_id": "macro_team",
        "gate_id": "expected_value_gate",
        "gate_status": "blocked",
        "observed_at": OBSERVED_AT,
        "reason_codes": ("liquidity_depth_blocked", "ev_negative_edge"),
        "source_reference": "https://public.example/research/candidate-alpha",
    }
    values.update(overrides)
    return module.StrategyRecommendationGateReasonRollupDigestInput(**values)


def report(*rows: object, cfg: object | None = None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_recommendation_gate_reason_rollup_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        items: list[object] = []
        for child in value.values():
            items.extend(walk(child))
        return tuple(items)
    if isinstance(value, list):
        items = []
        for child in value:
            items.extend(walk(child))
        return tuple(items)
    return (value,)


def test_empty_input_returns_clear_report_with_decimal_counts_and_flags() -> None:
    module = api()

    digest = report()

    assert is_dataclass(digest)
    assert digest.generated_at == GENERATED_AT
    assert digest.config_version == "strategy-recommendation-gate-reason-rollup-test-v0"
    assert digest.status == "clear"
    assert digest.reason_codes == ("gate_reason_rollup_clear",)
    assert digest.input_count == d("0")
    assert digest.candidate_count == d("0")
    assert digest.blocked_candidate_count == d("0")
    assert digest.watch_candidate_count == d("0")
    assert digest.pass_candidate_count == d("0")
    assert digest.failure_reason_code_count == d("0")
    assert digest.reason_code_counts == ()
    assert digest.category_rollups == ()
    assert digest.team_rollups == ()
    assert digest.top_blockers == ()
    assert digest.rows == ()
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True

    payload = module.strategy_recommendation_gate_reason_rollup_digest_payload(digest)
    assert payload["input_count"] == "0"
    assert payload["failure_reason_code_count"] == "0"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    json.dumps(payload, sort_keys=True)
    assert not any(isinstance(value, float) for value in walk(payload))
    assert not any(
        isinstance(value, int) and not isinstance(value, bool) for value in walk(payload)
    )


def test_rolls_up_reason_counts_category_team_and_top_blockers_deterministically() -> None:
    digest = report(
        gate_row(
            "candidate-beta",
            category_id="macro.policy",
            team_id="macro_team",
            gate_id="liquidity_gate",
            gate_status="blocked",
            reason_codes=("liquidity_depth_blocked", "ev_negative_edge", "ev_negative_edge"),
        ),
        gate_row(
            "candidate-alpha",
            category_id="macro.policy",
            team_id="macro_team",
            gate_id="risk_gate",
            gate_status="watch",
            reason_codes=("settlement_lag_watch",),
        ),
        gate_row(
            "candidate-alpha",
            category_id="macro.policy",
            team_id="risk_team",
            gate_id="evidence_gate",
            gate_status="blocked",
            reason_codes=("stale_evidence_blocked", "liquidity_depth_blocked"),
        ),
        gate_row(
            "candidate-gamma",
            category_id="sports.nfl",
            team_id="sports_team",
            gate_id="readiness_gate",
            gate_status="pass",
            reason_codes=("gate_passed",),
        ),
    )

    assert digest.status == "blocked"
    assert digest.input_count == d("4")
    assert digest.candidate_count == d("3")
    assert digest.blocked_candidate_count == d("2")
    assert digest.watch_candidate_count == d("0")
    assert digest.pass_candidate_count == d("1")
    assert digest.failure_reason_code_count == d("4")
    assert digest.reason_codes == (
        "ev_negative_edge",
        "liquidity_depth_blocked",
        "settlement_lag_watch",
        "stale_evidence_blocked",
    )
    assert digest.reason_code_counts == (
        ("liquidity_depth_blocked", d("2")),
        ("ev_negative_edge", d("1")),
        ("settlement_lag_watch", d("1")),
        ("stale_evidence_blocked", d("1")),
    )
    assert tuple(row.candidate_id for row in digest.rows) == (
        "candidate-alpha",
        "candidate-beta",
        "candidate-alpha",
        "candidate-gamma",
    )
    assert tuple(row.gate_id for row in digest.rows) == (
        "evidence_gate",
        "liquidity_gate",
        "risk_gate",
        "readiness_gate",
    )
    assert digest.rows[1].reason_codes == (
        "ev_negative_edge",
        "liquidity_depth_blocked",
    )

    assert tuple(
        (row.category_id, row.blocked_candidate_count, row.reason_codes)
        for row in digest.category_rollups
    ) == (
        (
            "macro.policy",
            d("2"),
            (
                "ev_negative_edge",
                "liquidity_depth_blocked",
                "settlement_lag_watch",
                "stale_evidence_blocked",
            ),
        ),
        ("sports.nfl", d("0"), ()),
    )
    assert tuple(
        (row.team_id, row.blocked_candidate_count, row.reason_codes)
        for row in digest.team_rollups
    ) == (
        (
            "macro_team",
            d("1"),
            ("ev_negative_edge", "liquidity_depth_blocked", "settlement_lag_watch"),
        ),
        ("risk_team", d("1"), ("liquidity_depth_blocked", "stale_evidence_blocked")),
        ("sports_team", d("0"), ()),
    )
    assert tuple(
        (row.reason_code, row.blocked_candidate_count, row.category_ids, row.team_ids)
        for row in digest.top_blockers
    ) == (
        (
            "liquidity_depth_blocked",
            d("2"),
            ("macro.policy",),
            ("macro_team", "risk_team"),
        ),
        ("ev_negative_edge", d("1"), ("macro.policy",), ("macro_team",)),
        ("stale_evidence_blocked", d("1"), ("macro.policy",), ("risk_team",)),
    )


def test_utc_normalization_rejects_naive_none_offset_and_datetime_subclasses() -> None:
    offset_digest = report(
        gate_row(
            observed_at=datetime(2026, 7, 4, 7, 30, tzinfo=timezone(timedelta(hours=-4))),
        ),
        generated_at=datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert offset_digest.generated_at == GENERATED_AT
    assert offset_digest.rows[0].observed_at == OBSERVED_AT

    with pytest.raises(ValueError, match="observed_at"):
        gate_row(observed_at=datetime(2026, 7, 4, 11, 30))
    with pytest.raises(ValueError, match="generated_at"):
        report(gate_row("aware"), generated_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        gate_row(observed_at=_DatetimeSubclass(2026, 7, 4, 11, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            gate_row("aware-subclass"),
            generated_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        gate_row(observed_at=datetime(2026, 7, 4, 11, 30, tzinfo=_NoneOffsetTz()))


def test_redacts_source_references_and_rejects_secret_like_public_text() -> None:
    module = api()
    secret = "postgres://paper:super-secret-token@localhost/polymarket"

    digest = report(gate_row("candidate-secret", source_reference=secret))
    payload = module.strategy_recommendation_gate_reason_rollup_digest_payload(digest)

    assert digest.rows[0].source_reference == "<redacted-source-reference>"
    assert payload["rows"][0]["source_reference"] == "<redacted-source-reference>"
    assert secret not in repr(digest)
    assert "secret" not in repr(digest).lower()
    assert secret not in json.dumps(payload, sort_keys=True)

    with pytest.raises(ValueError, match="candidate_id"):
        gate_row("secret-token-candidate")
    with pytest.raises(ValueError, match="gate_id"):
        gate_row("candidate-gate-secret", gate_id="private_key_gate")
    with pytest.raises(ValueError, match="reason_codes"):
        gate_row("candidate-reason-secret", reason_codes=("bearer_token_missing",))


def test_frozen_dataclasses_hard_flags_decimal_public_numbers_and_payload_validation() -> None:
    module = api()
    digest = report(gate_row("frozen"))

    for cls_name in (
        "StrategyRecommendationGateReasonRollupDigestConfig",
        "StrategyRecommendationGateReasonRollupDigestInput",
        "StrategyRecommendationGateReasonRollupDigestReasonCodeCount",
        "StrategyRecommendationGateReasonRollupDigestCategoryRollup",
        "StrategyRecommendationGateReasonRollupDigestTeamRollup",
        "StrategyRecommendationGateReasonRollupDigestTopBlocker",
        "StrategyRecommendationGateReasonRollupDigestReport",
    ):
        assert is_dataclass(getattr(module, cls_name))

    with pytest.raises(FrozenInstanceError):
        digest.status = "clear"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        digest.rows[0].candidate_id = "other"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        gate_row(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(digest, report_only=False)
    with pytest.raises(ValueError, match="candidate_count"):
        replace(digest, candidate_count=d("999"))
    with pytest.raises(ValueError, match="max_top_blockers"):
        config(max_top_blockers=3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="max_top_blockers"):
        config(max_top_blockers=_DecimalSubclass("3"))

    for item in (
        digest,
        *digest.rows,
        *digest.reason_code_counts,
        *digest.category_rollups,
        *digest.team_rollups,
        *digest.top_blockers,
    ):
        for field in fields(type(item)):
            value = getattr(item, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name

    with pytest.raises(ValueError, match="gate_status"):
        gate_row(gate_status="queued")
    with pytest.raises(ValueError, match="reason_codes"):
        gate_row(reason_codes=())
    with pytest.raises(ValueError, match="inputs"):
        report(gate_row("dup"), gate_row("dup"))
    with pytest.raises(ValueError, match="payload"):
        module.strategy_recommendation_gate_reason_rollup_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "input_count": 1,
            },
        )
    with pytest.raises(ValueError, match="readonly"):
        module.strategy_recommendation_gate_reason_rollup_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "rows": [{"paper_only": True, "report_only": True, "readonly": False}],
            },
        )


def test_static_reducer_has_no_io_or_execution_surface() -> None:
    source_path = Path(
        "src/polymarket_alpha_lab/strategy_recommendation_gate_reason_rollup_digest.py",
    )
    source = source_path.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_fragments = (
        "asyncio",
        "httpx",
        "requests",
        "socket",
        "sqlite",
        "psycopg",
        "urllib",
        "subprocess",
        "open(",
        "live",
        "trading",
        "auth",
        "wallet",
        "order",
        "cancel",
        "re" + "place",
        "private_key",
    )
    for fragment in forbidden_fragments:
        assert fragment not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
    assert not re.search(r"\b(auth|wallet|order|cancel|replace)\b", lowered)
