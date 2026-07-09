from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt):  # type: ignore[no-untyped-def]
        return None

    def dst(self, dt):  # type: ignore[no-untyped-def]
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_probability_depth_memory_guard_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate_ref(value: str) -> str:
    return f"candidate_ref_{sha256(value.encode('utf-8')).hexdigest()[:16]}"


def market_ref(value: str) -> str:
    return f"market_ref_{sha256(value.encode('utf-8')).hexdigest()[:16]}"


def source_ref(*parts: str) -> str:
    digest = sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"source_ref_{digest}"


def expected_payload_digest(payload: dict[str, object]) -> str:
    public_payload = dict(payload)
    public_payload.pop("payload_sha256")
    encoded = json.dumps(
        public_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def signed_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "generated_at": "2026-07-09T12:00:00+00:00",
        "config_version": "research-market-probability-depth-memory-guard-v0",
        "observation_count": "0",
        "pass_count": "0",
        "watch_count": "0",
        "block_count": "0",
        "max_cost_to_limit_ratio": "0.000000",
        "max_market_impact_probability": "0.000000",
        "mean_estimated_cost": "0.000000",
        "status": "pass",
        "reason_codes": ["market_probability_depth_memory_guard_clear"],
        "rows": [],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "payload_sha256": "0" * 64,
    }
    payload.update(overrides)
    payload["payload_sha256"] = expected_payload_digest(payload)
    return payload


def signed_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "candidate_ref": candidate_ref("candidate-secret-row"),
        "market_ref": market_ref("market-private-row"),
        "source_ref": source_ref("url", "text", "dsn", "table", "token"),
        "quoted_probability": "0.610000",
        "target_probability": "0.600000",
        "probability_gap": "0.010000",
        "available_depth": "100.000000",
        "estimated_cost": "10.000000",
        "memory_cost_limit": "100.000000",
        "cost_to_limit_ratio": "0.100000",
        "market_impact_probability": "0.010000",
        "age_hours": "1.000000",
        "status": "pass",
        "reason_codes": ["cost_depth_clear", "impact_clear", "memory_fresh"],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    row.update(overrides)
    return row


def config(**overrides: object):
    mod = api()
    values = {
        "config_version": "research-market-probability-depth-memory-guard-v0",
        "watch_cost_to_limit_ratio": d("0.500000"),
        "block_cost_to_limit_ratio": d("0.900000"),
        "watch_impact_probability": d("0.020000"),
        "block_impact_probability": d("0.050000"),
        "stale_age_hours": d("24.000000"),
    }
    values.update(overrides)
    return mod.ResearchMarketProbabilityDepthMemoryGuardConfig(**values)


def observation(**overrides: object):
    mod = api()
    values = {
        "raw_candidate_id": "candidate-secret-alpha",
        "raw_market_id": "market-private-alpha",
        "raw_source_url": "https://research.example.invalid/private?token=alpha",
        "raw_source_text": "internal source note alpha",
        "raw_source_dsn": "postgresql://user:pass@host/alpha",
        "raw_source_table": "internal_cost_table_alpha",
        "raw_source_token": "token-alpha",
        "quoted_probability": d("0.610000"),
        "target_probability": d("0.600000"),
        "available_depth": d("100.000000"),
        "estimated_cost": d("20.000000"),
        "memory_cost_limit": d("100.000000"),
        "market_impact_probability": d("0.010000"),
        "age_hours": d("2.000000"),
    }
    values.update(overrides)
    return mod.ResearchMarketProbabilityDepthMemoryGuardObservation(**values)


def report(*rows, cfg=None, generated_at: datetime = GENERATED_AT):
    return api().build_research_market_probability_depth_memory_guard_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_native_numbers(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_native_numbers(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_native_numbers(item)
        return
    if type(value) is bool:
        return
    assert type(value) is not float
    assert type(value) is not int


def test_report_summarizes_market_cost_depth_memory_guard_and_digest() -> None:
    built = report(
        observation(
            raw_candidate_id="candidate-secret-pass",
            raw_market_id="market-private-pass",
            estimated_cost=d("20.000000"),
            market_impact_probability=d("0.010000"),
            age_hours=d("2.000000"),
        ),
        observation(
            raw_candidate_id="candidate-secret-watch",
            raw_market_id="market-private-watch",
            estimated_cost=d("60.000000"),
            market_impact_probability=d("0.030000"),
            age_hours=d("30.000000"),
        ),
        observation(
            raw_candidate_id="candidate-secret-block",
            raw_market_id="market-private-block",
            estimated_cost=d("95.000000"),
            market_impact_probability=d("0.060000"),
            age_hours=d("1.000000"),
        ),
    )

    assert is_dataclass(built)
    assert built.generated_at == GENERATED_AT
    assert built.config_version == "research-market-probability-depth-memory-guard-v0"
    assert built.observation_count == d("3")
    assert built.pass_count == d("1")
    assert built.watch_count == d("1")
    assert built.block_count == d("1")
    assert built.max_cost_to_limit_ratio == d("0.950000")
    assert built.max_market_impact_probability == d("0.060000")
    assert built.mean_estimated_cost == d("58.333333")
    assert built.status == "block"
    assert built.reason_codes == (
        "depth_cost_block",
        "impact_block",
        "depth_cost_watch",
        "impact_watch",
        "memory_stale",
    )
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True

    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")
    first = built.rows[0]
    assert first.candidate_ref == candidate_ref("candidate-secret-block")
    assert first.market_ref == market_ref("market-private-block")
    assert first.probability_gap == d("0.010000")
    assert first.cost_to_limit_ratio == d("0.950000")
    assert first.reason_codes == ("depth_cost_block", "impact_block", "memory_fresh")

    payload = api().research_market_probability_depth_memory_guard_report_payload(built)
    assert payload["payload_sha256"] == expected_payload_digest(payload)
    assert built.payload_sha256 == payload["payload_sha256"]
    assert api().validate_research_market_probability_depth_memory_guard_report_payload(
        payload,
    )

    tampered = dict(payload)
    tampered["status"] = "pass"
    with pytest.raises(ValueError, match="payload_sha256"):
        api().validate_research_market_probability_depth_memory_guard_report_payload(
            tampered,
        )

    with pytest.raises(ValueError, match="payload_sha256"):
        replace(built, payload_sha256="0" * 64)


def test_empty_report_fails_closed_without_observations() -> None:
    built = report()

    assert built.observation_count == d("0")
    assert built.pass_count == d("0")
    assert built.watch_count == d("0")
    assert built.block_count == d("0")
    assert built.status == "block"
    assert built.reason_codes == ("no_observations",)
    assert api().validate_research_market_probability_depth_memory_guard_report_payload(
        built.payload,
    )


def test_payload_is_deterministic_decimal_only_and_redacts_raw_inputs() -> None:
    source_parts = (
        "https://research.example.invalid/private?token=bravo",
        "internal source note bravo",
        "postgresql://user:pass@host/bravo",
        "internal_cost_table_bravo",
        "token-bravo",
    )
    built = report(
        observation(
            raw_candidate_id="candidate-secret-bravo",
            raw_market_id="market-private-bravo",
            raw_source_url=source_parts[0],
            raw_source_text=source_parts[1],
            raw_source_dsn=source_parts[2],
            raw_source_table=source_parts[3],
            raw_source_token=source_parts[4],
        ),
        generated_at=datetime(2026, 7, 9, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload_one = api().research_market_probability_depth_memory_guard_report_payload(built)
    payload_two = api().research_market_probability_depth_memory_guard_report_payload(built)
    payload_text = repr(payload_one).lower()

    assert payload_one == payload_two
    assert built.generated_at == GENERATED_AT
    assert payload_one["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload_one["observation_count"] == "1"
    assert payload_one["rows"][0]["candidate_ref"] == candidate_ref(
        "candidate-secret-bravo",
    )
    assert payload_one["rows"][0]["market_ref"] == market_ref("market-private-bravo")
    assert payload_one["rows"][0]["source_ref"] == source_ref(*source_parts)
    assert payload_one["rows"][0]["estimated_cost"] == "20.000000"
    assert_no_native_numbers(payload_one)
    assert "Decimal(" not in repr(payload_one)
    assert "datetime" not in payload_text

    for raw_fragment in (
        "candidate-secret-bravo",
        "market-private-bravo",
        "research.example.invalid",
        "internal source note bravo",
        "postgresql://",
        "internal_cost_table_bravo",
        "token-bravo",
        "raw_candidate_id",
        "raw_market_id",
        "raw_source_url",
        "raw_source_text",
        "raw_source_dsn",
        "raw_source_table",
        "raw_source_token",
    ):
        assert raw_fragment.lower() not in payload_text


def test_statuses_are_limited_and_public_dicts_reject_unsafe_surfaces() -> None:
    mod = api()

    assert mod.STATUSES == ("pass", "watch", "block")

    with pytest.raises(ValueError, match="status is not supported"):
        mod.ResearchMarketProbabilityDepthMemoryGuardRow(
            candidate_ref=candidate_ref("candidate-secret"),
            market_ref=market_ref("market-secret"),
            source_ref=source_ref("url", "text", "dsn", "table", "token"),
            quoted_probability=d("0.610000"),
            target_probability=d("0.600000"),
            probability_gap=d("0.010000"),
            available_depth=d("100.000000"),
            estimated_cost=d("10.000000"),
            memory_cost_limit=d("100.000000"),
            cost_to_limit_ratio=d("0.100000"),
            market_impact_probability=d("0.010000"),
            age_hours=d("1.000000"),
            status="review",
            reason_codes=("cost_depth_clear", "impact_clear", "memory_fresh"),
        )

    with pytest.raises(ValueError, match="unsafe public field"):
        mod.research_market_probability_depth_memory_guard_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "payload_sha256": "0" * 64,
                "raw_candidate_id": "candidate-secret",
            },
        )

    for unsafe_key in (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "question",
        "source_url",
        "source_text",
        "source_dsn",
        "source_table",
        "source_token",
        "execution_surface",
        "live_surface",
    ):
        with pytest.raises(ValueError, match="unsafe public field"):
            mod.research_market_probability_depth_memory_guard_report_payload(
                {
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                    "payload_sha256": "0" * 64,
                    unsafe_key: "raw-value",
                },
            )

    for unsafe_value in (
        "wallet address",
        "order surface",
        "trade ticket",
        "sizing input",
        "recommendation text",
        "execution note",
        "live surface",
        "internal_cost_table_bravo",
        "internal source note bravo",
    ):
        with pytest.raises(ValueError, match="sensitive value"):
            mod.research_market_probability_depth_memory_guard_report_payload(
                {
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                    "payload_sha256": "0" * 64,
                    "public_note": unsafe_value,
                },
            )

    with pytest.raises(ValueError, match="payload must be readonly"):
        mod.research_market_probability_depth_memory_guard_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": False,
                "payload_sha256": "0" * 64,
            },
        )


def test_validate_payload_rejects_signed_public_shape_violations() -> None:
    mod = api()

    with pytest.raises(ValueError, match="status is not supported"):
        mod.validate_research_market_probability_depth_memory_guard_report_payload(
            signed_payload(status="review"),
        )

    with pytest.raises(ValueError, match="row must be readonly"):
        mod.validate_research_market_probability_depth_memory_guard_report_payload(
            signed_payload(
                observation_count="1",
                pass_count="1",
                rows=[signed_row(readonly=False)],
            ),
        )

    with pytest.raises(ValueError, match="unsafe public field"):
        mod.validate_research_market_probability_depth_memory_guard_report_payload(
            signed_payload(execution_surface="disabled"),
        )


def test_report_payload_helper_rejects_non_schema_fields() -> None:
    mod = api()

    with pytest.raises(ValueError, match="unsupported public fields"):
        mod.research_market_probability_depth_memory_guard_report_payload(
            signed_payload(public_note="benign"),
        )

    with pytest.raises(ValueError, match="unsupported public fields"):
        mod.research_market_probability_depth_memory_guard_report_payload(
            signed_payload(
                observation_count="1",
                pass_count="1",
                status="pass",
                reason_codes=["market_probability_depth_memory_guard_clear"],
                rows=[signed_row(public_note="benign")],
            ),
        )


def test_config_version_is_supported_exactly() -> None:
    mod = api()
    unsupported_version = "research-market-probability-depth-memory-guard-v1"

    with pytest.raises(ValueError, match="supported config version"):
        config(config_version=unsupported_version)

    with pytest.raises(ValueError, match="supported config version"):
        mod.validate_research_market_probability_depth_memory_guard_report_payload(
            signed_payload(config_version=unsupported_version),
        )


def test_public_dataclasses_reject_subclassing() -> None:
    mod = api()

    for public_type in (
        mod.ResearchMarketProbabilityDepthMemoryGuardConfig,
        mod.ResearchMarketProbabilityDepthMemoryGuardObservation,
        mod.ResearchMarketProbabilityDepthMemoryGuardRow,
        mod.ResearchMarketProbabilityDepthMemoryGuardReport,
    ):
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Unsafe{public_type.__name__}", (public_type,), {})


def test_decimal_only_flags_and_frozen_validation() -> None:
    built = report(observation())

    with pytest.raises(FrozenInstanceError):
        built.status = "pass"  # type: ignore[misc]

    with pytest.raises(ValueError, match="quoted_probability must be a Decimal"):
        observation(quoted_probability=0.61)

    with pytest.raises(ValueError, match="quoted_probability must be a Decimal"):
        observation(quoted_probability=_DecimalSubclass("0.610000"))

    with pytest.raises(ValueError, match="quoted_probability must be finite"):
        observation(quoted_probability=Decimal("NaN"))

    with pytest.raises(ValueError, match="memory_cost_limit must be positive"):
        observation(memory_cost_limit=d("0.000000"))

    with pytest.raises(ValueError, match="config must be paper_only"):
        config(paper_only=False)

    with pytest.raises(ValueError, match="observation must be readonly"):
        observation(readonly=False)

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(
            observation(),
            generated_at=datetime(2026, 7, 9, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )


def test_module_scope_has_no_forbidden_runtime_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/"
        "research_market_probability_depth_memory_guard_report.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "network",
        "database",
        "db",
        "order",
        "trade",
        "trading",
        "sizing",
        "recommendation",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
