from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, tzinfo
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_market_signal_arbitration_readiness_report"
)
GENERATED_AT = datetime(2026, 7, 8, 15, 45, tzinfo=UTC)


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "agreement_weight": d("0.400000"),
        "source_confidence_weight": d("0.300000"),
        "cost_clearance_weight": d("0.300000"),
        "pass_disagreement_ceiling": d("0.080000"),
        "block_disagreement_floor": d("0.250000"),
        "pass_source_confidence_floor": d("0.700000"),
        "block_source_confidence_ceiling": d("0.450000"),
        "pass_cost_pressure_ceiling": d("0.150000"),
        "block_cost_pressure_floor": d("0.450000"),
        "pass_score_floor": d("0.750000"),
        "watch_score_floor": d("0.550000"),
    }
    values.update(overrides)
    return module.ResearchStrategyMarketSignalArbitrationReadinessConfig(**values)


def signal(**overrides: object) -> Any:
    module = api()
    values = {
        "signal_ref": "sig-pass",
        "model_probability": d("0.620000"),
        "team_consensus_probability": d("0.600000"),
        "source_confidence": d("0.850000"),
        "market_implied_probability": d("0.590000"),
        "fee_pressure": d("0.050000"),
        "spread_pressure": d("0.100000"),
        "slippage_pressure": d("0.050000"),
        "observed_at": GENERATED_AT,
    }
    values.update(overrides)
    return module.ResearchStrategyMarketSignalArbitrationInput(**values)


def report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_strategy_market_signal_arbitration_readiness_report(
        rows,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def assert_numeric_fields_are_decimal(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if type(item) is bool:
            continue
        assert type(item) is not float
        assert type(item) is not int
        if isinstance(item, tuple):
            for nested in item:
                if is_dataclass(nested):
                    assert_numeric_fields_are_decimal(nested)


def assert_no_float_or_int_values(value: object) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def payload_digest(payload: dict[str, Any], *, digest_key: str) -> str:
    values = {key: item for key, item in payload.items() if key != digest_key}
    encoded = json.dumps(values, sort_keys=True, separators=(",", ":")).encode(
        "utf-8",
    )
    return sha256(encoded).hexdigest()


def test_arbitrates_pass_watch_block_rows_with_decimal_scores() -> None:
    result = report(
        signal(
            signal_ref="sig-watch",
            model_probability=d("0.720000"),
            team_consensus_probability=d("0.600000"),
            source_confidence=d("0.700000"),
            market_implied_probability=d("0.640000"),
            fee_pressure=d("0.200000"),
            spread_pressure=d("0.200000"),
            slippage_pressure=d("0.200000"),
        ),
        signal(),
        signal(
            signal_ref="sig-block",
            model_probability=d("0.900000"),
            team_consensus_probability=d("0.550000"),
            source_confidence=d("0.400000"),
            market_implied_probability=d("0.600000"),
            fee_pressure=d("0.500000"),
            spread_pressure=d("0.400000"),
            slippage_pressure=d("0.450000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == (
        "research-strategy-market-signal-arbitration-readiness-report-v1"
    )
    assert result.signal_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.mean_arbitration_score == d("0.756667")
    assert result.max_disagreement_pressure == d("0.350000")
    assert result.max_cost_pressure == d("0.450000")
    assert result.report_status == "block"
    assert result.reason_codes == (
        "disagreement_pressure_block",
        "source_confidence_block",
        "cost_pressure_block",
        "arbitration_score_block",
        "disagreement_pressure_watch",
        "cost_pressure_watch",
        "arbitration_readiness_pass",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.public_digest)
    assert_numeric_fields_are_decimal(result)

    assert tuple(row.signal_ref for row in result.rows) == (
        "sig-block",
        "sig-watch",
        "sig-pass",
    )

    blocked = result.rows[0]
    assert blocked.status == "block"
    assert blocked.model_team_gap == d("0.350000")
    assert blocked.model_market_gap == d("0.300000")
    assert blocked.team_market_gap == d("0.050000")
    assert blocked.disagreement_pressure == d("0.350000")
    assert blocked.cost_pressure == d("0.450000")
    assert blocked.arbitration_score == d("0.545000")
    assert blocked.reason_codes == (
        "disagreement_pressure_block",
        "source_confidence_block",
        "cost_pressure_block",
        "arbitration_score_block",
    )
    assert_digest(blocked.validation_digest)

    watched = result.rows[1]
    assert watched.status == "watch"
    assert watched.model_team_gap == d("0.120000")
    assert watched.model_market_gap == d("0.080000")
    assert watched.team_market_gap == d("0.040000")
    assert watched.disagreement_pressure == d("0.120000")
    assert watched.cost_pressure == d("0.200000")
    assert watched.arbitration_score == d("0.802000")
    assert watched.reason_codes == (
        "disagreement_pressure_watch",
        "cost_pressure_watch",
    )

    passed = result.rows[2]
    assert passed.status == "pass"
    assert passed.model_team_gap == d("0.020000")
    assert passed.model_market_gap == d("0.030000")
    assert passed.team_market_gap == d("0.010000")
    assert passed.disagreement_pressure == d("0.030000")
    assert passed.cost_pressure == d("0.066667")
    assert passed.arbitration_score == d("0.923000")
    assert passed.reason_codes == ("arbitration_readiness_pass",)


def test_disagreement_and_cost_boundaries_are_deterministic() -> None:
    result = report(
        signal(
            signal_ref="sig-boundary-pass",
            model_probability=d("0.580000"),
            team_consensus_probability=d("0.500000"),
            source_confidence=d("0.700000"),
            market_implied_probability=d("0.540000"),
            fee_pressure=d("0.150000"),
            spread_pressure=d("0.150000"),
            slippage_pressure=d("0.150000"),
        ),
        signal(
            signal_ref="sig-boundary-watch",
            model_probability=d("0.580001"),
            team_consensus_probability=d("0.500000"),
            source_confidence=d("0.700000"),
            market_implied_probability=d("0.540000"),
            fee_pressure=d("0.150001"),
            spread_pressure=d("0.150001"),
            slippage_pressure=d("0.150001"),
        ),
        signal(
            signal_ref="sig-boundary-block",
            model_probability=d("0.750000"),
            team_consensus_probability=d("0.500000"),
            source_confidence=d("0.700000"),
            market_implied_probability=d("0.600000"),
            fee_pressure=d("0.150000"),
            spread_pressure=d("0.150000"),
            slippage_pressure=d("0.150000"),
        ),
    )

    by_ref = {row.signal_ref: row for row in result.rows}
    assert by_ref["sig-boundary-pass"].status == "pass"
    assert by_ref["sig-boundary-pass"].disagreement_pressure == d("0.080000")
    assert by_ref["sig-boundary-pass"].cost_pressure == d("0.150000")
    assert by_ref["sig-boundary-pass"].arbitration_score == d("0.833000")
    assert by_ref["sig-boundary-pass"].reason_codes == (
        "arbitration_readiness_pass",
    )

    assert by_ref["sig-boundary-watch"].status == "watch"
    assert by_ref["sig-boundary-watch"].disagreement_pressure == d("0.080001")
    assert by_ref["sig-boundary-watch"].cost_pressure == d("0.150001")
    assert by_ref["sig-boundary-watch"].reason_codes == (
        "disagreement_pressure_watch",
        "cost_pressure_watch",
    )

    assert by_ref["sig-boundary-block"].status == "block"
    assert by_ref["sig-boundary-block"].disagreement_pressure == d("0.250000")
    assert by_ref["sig-boundary-block"].reason_codes == (
        "disagreement_pressure_block",
    )


def test_public_payload_and_digest_are_stable_and_revalidated() -> None:
    module = api()
    result = report(
        signal(signal_ref="sig-pass-b"),
        signal(
            signal_ref="sig-watch-b",
            model_probability=d("0.720000"),
            team_consensus_probability=d("0.600000"),
            source_confidence=d("0.700000"),
            market_implied_probability=d("0.640000"),
            fee_pressure=d("0.200000"),
            spread_pressure=d("0.200000"),
            slippage_pressure=d("0.200000"),
        ),
    )
    same_result = report(
        signal(
            signal_ref="sig-watch-b",
            model_probability=d("0.720000"),
            team_consensus_probability=d("0.600000"),
            source_confidence=d("0.700000"),
            market_implied_probability=d("0.640000"),
            fee_pressure=d("0.200000"),
            spread_pressure=d("0.200000"),
            slippage_pressure=d("0.200000"),
        ),
        signal(signal_ref="sig-pass-b"),
    )

    assert same_result.public_digest == result.public_digest
    assert (
        module.research_strategy_market_signal_arbitration_readiness_report_digest(
            result,
        )
        == result.public_digest
    )

    payload = (
        module.research_strategy_market_signal_arbitration_readiness_report_public_payload(
            result,
        )
    )
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)
    assert payload["generated_at"] == "2026-07-08T15:45:00+00:00"
    assert payload["signal_count"] == "2"
    assert payload["rows"][0]["validation_digest"] == result.rows[0].validation_digest
    assert payload["public_digest"] == result.public_digest
    assert_no_float_or_int_values(payload)
    assert (
        module.research_strategy_market_signal_arbitration_readiness_report_public_payload(
            payload,
        )
        == payload
    )
    assert "sig-watch-b" in encoded

    tampered = {**payload, "pass_count": "99"}
    with pytest.raises(ValueError, match="public_digest"):
        module.research_strategy_market_signal_arbitration_readiness_report_public_payload(
            tampered,
        )

    with pytest.raises(ValueError, match="validation_digest"):
        replace(result.rows[0], validation_digest="0" * 64)

    with pytest.raises(ValueError, match="public_digest"):
        replace(result, public_digest="0" * 64)

    extra_payload = {**payload, "diagnostic_note": "looks-safe"}
    extra_payload["public_digest"] = payload_digest(
        extra_payload,
        digest_key="public_digest",
    )
    with pytest.raises(ValueError, match="unexpected public payload keys"):
        module.research_strategy_market_signal_arbitration_readiness_report_public_payload(
            extra_payload,
        )

    extra_row = {**payload["rows"][0], "diagnostic_note": "looks-safe"}
    extra_row["validation_digest"] = payload_digest(
        extra_row,
        digest_key="validation_digest",
    )
    extra_row_payload = {**payload, "rows": [extra_row]}
    extra_row_payload["public_digest"] = payload_digest(
        extra_row_payload,
        digest_key="public_digest",
    )
    with pytest.raises(ValueError, match="unexpected public row keys"):
        module.research_strategy_market_signal_arbitration_readiness_report_public_payload(
            extra_row_payload,
        )

    drifted_payload = {
        **payload,
        "pass_count": "99",
    }
    drifted_payload["public_digest"] = payload_digest(
        drifted_payload,
        digest_key="public_digest",
    )
    with pytest.raises(ValueError, match="pass_count must match rows"):
        module.research_strategy_market_signal_arbitration_readiness_report_public_payload(
            drifted_payload,
        )

    duplicate_reason_row = {
        **payload["rows"][0],
        "reason_codes": [
            payload["rows"][0]["reason_codes"][0],
            payload["rows"][0]["reason_codes"][0],
        ],
    }
    duplicate_reason_row["validation_digest"] = payload_digest(
        duplicate_reason_row,
        digest_key="validation_digest",
    )
    duplicate_reason_payload = {**payload, "rows": [duplicate_reason_row]}
    duplicate_reason_payload["public_digest"] = payload_digest(
        duplicate_reason_payload,
        digest_key="public_digest",
    )
    with pytest.raises(ValueError, match="reason_codes must be unique"):
        module.research_strategy_market_signal_arbitration_readiness_report_public_payload(
            duplicate_reason_payload,
        )


def test_public_payload_rejects_leaks_and_non_decimal_numeric_surfaces() -> None:
    module = api()
    result = report(signal())
    payload = (
        module.research_strategy_market_signal_arbitration_readiness_report_public_payload(
            result,
        )
    )
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    forbidden_public_terms = (
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "https://",
        "postgres://",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "sizing",
        "recommend",
    )
    for term in forbidden_public_terms:
        assert term not in encoded

    unsafe_payloads = (
        {**payload, "raw_candidate_id": "abc"},
        {**payload, "candidate_id": "abc"},
        {**payload, "candidateId": "abc"},
        {**payload, "market_id": "abc"},
        {**payload, "marketId": "abc"},
        {**payload, "market_slug": "abc"},
        {**payload, "marketSlug": "abc"},
        {**payload, "question": "abc"},
        {**payload, "source_url": "https://example.test/path"},
        {**payload, "sourceUrl": "https://example.test/path"},
        {**payload, "source_text": "raw"},
        {**payload, "sourceText": "raw"},
        {**payload, "storage": "postgres://example.test/db"},
        {**payload, "dsn": "postgres://example.test/db"},
        {**payload, "table_name": "abc"},
        {**payload, "tableName": "abc"},
        {**payload, "token": "secret"},
        {**payload, "apiKey": "secret"},
        {**payload, "privateKey": "secret"},
        {**payload, "wallet": "abc"},
        {**payload, "order": "abc"},
        {**payload, "trade": "abc"},
        {**payload, "live": "abc"},
        {**payload, "sizing": "abc"},
        {**payload, "recommendation": "abc"},
    )
    for unsafe_payload in unsafe_payloads:
        with pytest.raises(ValueError, match="unsafe"):
            module.research_strategy_market_signal_arbitration_readiness_report_public_payload(
                unsafe_payload,
            )

    with pytest.raises(ValueError, match="readonly"):
        module.research_strategy_market_signal_arbitration_readiness_report_public_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="numeric"):
        module.research_strategy_market_signal_arbitration_readiness_report_public_payload(
            {**payload, "signal_count": 1},
        )
    with pytest.raises(ValueError, match="numeric"):
        module.research_strategy_market_signal_arbitration_readiness_report_public_payload(
            {**payload, "mean_arbitration_score": 1.0},
        )

    with pytest.raises(ValueError, match="unsafe"):
        signal(signal_ref="market_id-alpha")
    with pytest.raises(ValueError, match="raw identifier"):
        signal(signal_ref="550e8400-e29b-41d4-a716-446655440000")
    with pytest.raises(ValueError, match="unsafe"):
        signal(signal_ref="https://example.test/raw")


def test_custom_config_and_invalid_inputs_are_validated() -> None:
    module = api()
    custom = config(
        agreement_weight=d("0.500000"),
        source_confidence_weight=d("0.250000"),
        cost_clearance_weight=d("0.250000"),
    )
    result = report(signal(), cfg=custom)
    assert result.rows[0].arbitration_score == d("0.930833")

    stricter = config(pass_score_floor=d("0.950000"))
    stricter_result = report(signal(), cfg=stricter)
    assert stricter_result.rows[0].status == "watch"
    assert stricter_result.rows[0].reason_codes == ("arbitration_score_watch",)

    with pytest.raises(ValueError, match="agreement_weight must be a Decimal"):
        config(agreement_weight=0.4)
    with pytest.raises(ValueError, match="weights must sum"):
        config(cost_clearance_weight=d("0.200000"))
    with pytest.raises(ValueError, match="pass_disagreement_ceiling"):
        config(
            pass_disagreement_ceiling=d("0.300000"),
            block_disagreement_floor=d("0.250000"),
        )
    with pytest.raises(ValueError, match="block_source_confidence_ceiling"):
        config(
            pass_source_confidence_floor=d("0.700000"),
            block_source_confidence_ceiling=d("0.750000"),
        )
    with pytest.raises(ValueError, match="pass_cost_pressure_ceiling"):
        config(
            pass_cost_pressure_ceiling=d("0.500000"),
            block_cost_pressure_floor=d("0.450000"),
        )
    with pytest.raises(ValueError, match="pass_score_floor"):
        config(pass_score_floor=d("0.500000"), watch_score_floor=d("0.550000"))
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="model_probability must be a Decimal"):
        signal(model_probability=1)
    with pytest.raises(ValueError, match="source_confidence"):
        signal(source_confidence=d("-0.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        signal(paper_only=False)

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_strategy_market_signal_arbitration_readiness_report(
            (signal(),),
            config=config(),
            generated_at=datetime(2026, 7, 8, 15, 45),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_strategy_market_signal_arbitration_readiness_report(
            (signal(),),
            config=config(),
            generated_at=datetime(2026, 7, 8, 15, 45, tzinfo=_NoneOffsetTimezone()),
        )

    with pytest.raises(ValueError, match="signal_ref values must be unique"):
        report(signal(), signal())

    with pytest.raises(ValueError, match="observed_at values must be at or before generated_at"):
        module.build_research_strategy_market_signal_arbitration_readiness_report(
            (signal(observed_at=datetime(2026, 7, 8, 15, 45, 1, tzinfo=UTC)),),
            config=config(),
            generated_at=GENERATED_AT,
        )

    result = report(signal())
    with pytest.raises(FrozenInstanceError):
        result.rows[0].status = "block"
    with pytest.raises(ValueError, match="reason_codes must be unique"):
        replace(
            result.rows[0],
            reason_codes=(
                "arbitration_readiness_pass",
                "arbitration_readiness_pass",
            ),
        )


def test_module_scope_is_report_only_readonly_and_public_api_is_narrow() -> None:
    module = api()
    path = Path(
        "src/polymarket_alpha_lab/"
        "research_strategy_market_signal_arbitration_readiness_report.py",
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))

    banned_imports = {
        "asyncio",
        "http",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    banned_calls = {
        "connect",
        "delete",
        "execute",
        "insert",
        "login",
        "open",
        "post",
        "request",
        "send",
        "submit",
        "update",
        "urlopen",
        "write",
    }
    banned_attributes = banned_calls | {"commit", "rollback", "session"}
    forbidden_public_name_fragments = (
        "candidate",
        "market_id",
        "market_slug",
        "question",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "position",
        "sizing",
        "recommend",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_calls
        elif isinstance(node, ast.Attribute):
            assert node.attr not in banned_attributes

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_MARKET_SIGNAL_ARBITRATION_READINESS_CONFIG_VERSION",
        "ResearchStrategyMarketSignalArbitrationInput",
        "ResearchStrategyMarketSignalArbitrationReadinessConfig",
        "ResearchStrategyMarketSignalArbitrationReadinessReport",
        "ResearchStrategyMarketSignalArbitrationReadinessRow",
        "build_research_strategy_market_signal_arbitration_readiness_report",
        "research_strategy_market_signal_arbitration_readiness_report_digest",
        "research_strategy_market_signal_arbitration_readiness_report_public_payload",
    )
    for public_name in module.__all__:
        assert [
            fragment
            for fragment in forbidden_public_name_fragments
            if fragment in public_name.lower()
        ] == []
