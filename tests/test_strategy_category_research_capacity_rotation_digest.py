from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timezone, timedelta, tzinfo
from decimal import Decimal

import pytest


GENERATED_AT_EST = datetime(
    2026,
    7,
    2,
    10,
    30,
    tzinfo=timezone(timedelta(hours=-4)),
)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_category_research_capacity_rotation_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def signal(
    category_id: str,
    strategy_id: str,
    *,
    rotation_status: str = "stable",
    liquidity_share_ratio_delta: str = "0.000000",
    ending_liquidity_share_ratio: str = "0.100000",
    queue_count: str = "0",
    available_analyst_agent_slots: str = "1",
    capacity_gap_count: str = "0",
    source_row_count: str = "1",
    source_missing: bool = False,
):
    digest = api()
    return digest.StrategyCategoryResearchCapacityRotationSignal(
        category_id=category_id,
        strategy_id=strategy_id,
        rotation_status=rotation_status,
        liquidity_share_ratio_delta=d(liquidity_share_ratio_delta),
        ending_liquidity_share_ratio=d(ending_liquidity_share_ratio),
        queue_count=d(queue_count),
        available_analyst_agent_slots=d(available_analyst_agent_slots),
        capacity_gap_count=d(capacity_gap_count),
        source_row_count=d(source_row_count),
        source_missing=source_missing,
    )


def report(*signals):
    digest = api()
    return digest.build_strategy_category_research_capacity_rotation_digest(
        signals,
        config=digest.StrategyCategoryResearchCapacityRotationDigestConfig(),
        generated_at=GENERATED_AT_EST,
    )


def test_reduces_capacity_rotation_signals_to_deterministic_digest_rows() -> None:
    digest_report = report(
        signal(
            "crypto",
            "btc-liquidity",
            rotation_status="rotating_in",
            liquidity_share_ratio_delta="0.120000",
            ending_liquidity_share_ratio="0.450000",
            queue_count="5",
            available_analyst_agent_slots="2",
            capacity_gap_count="2",
        ),
        signal(
            "politics",
            "election-recheck",
            rotation_status="rotating_in",
            liquidity_share_ratio_delta="0.080000",
            ending_liquidity_share_ratio="0.250000",
            queue_count="2",
            available_analyst_agent_slots="2",
        ),
        signal(
            "sports",
            "fixture-refresh",
            rotation_status="rotating_out",
            liquidity_share_ratio_delta="-0.060000",
            ending_liquidity_share_ratio="0.050000",
            queue_count="1",
            available_analyst_agent_slots="3",
        ),
        signal(
            "macro",
            "rates-watch",
            rotation_status="stable",
            liquidity_share_ratio_delta="0.000000",
            ending_liquidity_share_ratio="0.150000",
            queue_count="1",
            available_analyst_agent_slots="4",
        ),
    )

    assert is_dataclass(digest_report)
    assert digest_report.generated_at == datetime(2026, 7, 2, 14, 30, tzinfo=UTC)
    assert (
        digest_report.config_version
        == "strategy-category-research-capacity-rotation-digest-v0"
    )
    assert digest_report.source_signal_count == d("4")
    assert digest_report.digest_row_count == d("4")
    assert digest_report.pass_row_count == d("2")
    assert digest_report.watch_row_count == d("1")
    assert digest_report.blocked_row_count == d("1")
    assert digest_report.source_missing_count == d("0")
    assert digest_report.digest_status == "blocked"
    assert digest_report.reason_codes == (
        "strategy_category_research_capacity_rotation_blocked",
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True

    blocked = digest_report.digest_rows[0]
    assert blocked.redacted_category_ref == "<redacted-category-001>"
    assert blocked.redacted_strategy_ref == "<redacted-strategy-001>"
    assert blocked.rotation_status == "rotating_in"
    assert blocked.liquidity_share_ratio_delta == d("0.120000")
    assert blocked.ending_liquidity_share_ratio == d("0.450000")
    assert blocked.queue_count == d("5")
    assert blocked.available_analyst_agent_slots == d("2")
    assert blocked.capacity_gap_count == d("2")
    assert blocked.capacity_pressure_ratio == d("2.500000")
    assert blocked.slot_coverage_ratio == d("0.400000")
    assert blocked.rotation_capacity_status == "blocked"
    assert blocked.reason_codes == (
        "rotation_in_capacity_blocked",
        "capacity_gap_present",
        "low_slot_coverage",
        "capacity_pressure_blocked",
    )

    watch = digest_report.digest_rows[1]
    assert watch.redacted_category_ref == "<redacted-category-003>"
    assert watch.rotation_capacity_status == "watch"
    assert watch.reason_codes == (
        "rotation_in_capacity_watch",
        "capacity_pressure_watch",
    )

    released = digest_report.digest_rows[2]
    assert released.redacted_category_ref == "<redacted-category-004>"
    assert released.rotation_capacity_status == "pass"
    assert released.reason_codes == ("rotation_out_capacity_release",)

    report_text = repr(digest_report)
    for sensitive_token in (
        "btc-liquidity",
        "election-recheck",
        "fixture-refresh",
        "rates-watch",
    ):
        assert sensitive_token not in report_text


def test_empty_digest_is_readonly_pass_with_decimal_zero_counts() -> None:
    digest_report = report()

    assert digest_report.source_signal_count == d("0")
    assert digest_report.digest_row_count == d("0")
    assert digest_report.pass_row_count == d("0")
    assert digest_report.watch_row_count == d("0")
    assert digest_report.blocked_row_count == d("0")
    assert digest_report.source_missing_count == d("0")
    assert digest_report.digest_status == "pass"
    assert digest_report.reason_codes == (
        "strategy_category_research_capacity_rotation_clear",
    )
    assert digest_report.digest_rows == ()
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_source_missing_is_watch_only_and_public_output_stays_redacted() -> None:
    secret_category = "secret-category"
    secret_strategy = "secret-strategy"
    digest_report = report(
        signal(
            secret_category,
            secret_strategy,
            rotation_status="rotating_in",
            liquidity_share_ratio_delta="0.500000",
            ending_liquidity_share_ratio="0.800000",
            queue_count="9",
            available_analyst_agent_slots="0",
            capacity_gap_count="9",
            source_row_count="0",
            source_missing=True,
        ),
    )

    row = digest_report.digest_rows[0]
    assert digest_report.digest_status == "watch"
    assert digest_report.reason_codes == (
        "strategy_category_research_capacity_rotation_watch",
        "strategy_category_research_capacity_rotation_source_missing",
    )
    assert digest_report.source_missing_count == d("1")
    assert row.rotation_capacity_status == "watch"
    assert row.reason_codes == (
        "strategy_category_research_capacity_rotation_source_missing",
    )
    assert row.redacted_category_ref == "<redacted-category-001>"
    assert row.redacted_strategy_ref == "<redacted-strategy-001>"
    assert secret_category not in repr(digest_report)
    assert secret_strategy not in repr(digest_report)


def test_payload_is_json_ready_decimal_stringed_and_omits_unsafe_surfaces() -> None:
    digest = api()
    digest_report = report(
        signal(
            "crypto",
            "eth-capacity",
            rotation_status="rotating_in",
            liquidity_share_ratio_delta="0.100000",
            ending_liquidity_share_ratio="0.300000",
            queue_count="3",
            available_analyst_agent_slots="3",
        ),
    )

    payload = digest.strategy_category_research_capacity_rotation_digest_payload(
        digest_report,
    )
    payload_text = repr(payload).lower()

    assert "eth-capacity" not in payload_text
    assert "market_slug" not in payload_text
    assert "question" not in payload_text
    assert "recommend" not in payload_text
    assert "advice" not in payload_text
    assert "wallet" not in payload_text
    assert "order" not in payload_text
    assert payload["source_signal_count"] == "1"
    assert payload["digest_rows"][0]["redacted_strategy_ref"] == "<redacted-strategy-001>"
    assert payload["digest_rows"][0]["capacity_pressure_ratio"] == "1.000000"
    assert payload["paper_only"] is True


def test_payload_accepts_readonly_dicts_and_rejects_flag_or_numeric_drift() -> None:
    digest = api()

    generated_payload = digest.strategy_category_research_capacity_rotation_digest_payload(
        report(
            signal(
                "crypto",
                "eth-capacity",
                rotation_status="rotating_in",
                liquidity_share_ratio_delta="0.100000",
                ending_liquidity_share_ratio="0.300000",
                queue_count="3",
                available_analyst_agent_slots="3",
            ),
        ),
    )
    payload = digest.strategy_category_research_capacity_rotation_digest_payload(
        generated_payload,
    )

    assert payload["generated_at"] == "2026-07-02T14:30:00+00:00"
    assert payload["source_signal_count"] == "1"
    assert payload["digest_rows"][0]["capacity_pressure_ratio"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    with pytest.raises(ValueError, match="paper_only"):
        digest.strategy_category_research_capacity_rotation_digest_payload(
            {**generated_payload, "paper_only": False},
        )

    with pytest.raises(ValueError, match="Decimal"):
        digest.strategy_category_research_capacity_rotation_digest_payload(
            {**generated_payload, "source_signal_count": 1},
        )


def test_payload_and_reason_codes_reject_unsafe_or_secret_like_text() -> None:
    digest = api()

    for payload in (
        {
            "wallet_address": "redacted",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "reason_codes": ("private_key_leak",),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "note": "send live trading order",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ):
        with pytest.raises(ValueError, match="unsafe|sensitive|secret"):
            digest.strategy_category_research_capacity_rotation_digest_payload(payload)

    row = report(signal("macro", "rates")).digest_rows[0]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(row, reason_codes=("wallet_secret",))

    with pytest.raises(ValueError, match="redacted_category_ref must be redacted"):
        replace(row, redacted_category_ref="<redacted-category-secret>")


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    digest = api()
    row = report(signal("macro", "rates")).digest_rows[0]

    assert is_dataclass(row)
    with pytest.raises(FrozenInstanceError):
        row.queue_count = d("2")  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="queue_count must be a Decimal"):
        digest.StrategyCategoryResearchCapacityRotationSignal(
            category_id="crypto",
            strategy_id="btc",
            rotation_status="stable",
            liquidity_share_ratio_delta=d("0.000000"),
            ending_liquidity_share_ratio=d("0.100000"),
            queue_count=1,
            available_analyst_agent_slots=d("1"),
            capacity_gap_count=d("0"),
        )

    class DerivedDecimal(Decimal):
        pass

    with pytest.raises(ValueError, match="min_rotation_in_share_delta"):
        digest.StrategyCategoryResearchCapacityRotationDigestConfig(
            min_rotation_in_share_delta=DerivedDecimal("0.050000"),
        )

    with pytest.raises(ValueError, match="duplicate category strategy pairs"):
        report(signal("crypto", "btc"), signal("crypto", "btc"))

    with pytest.raises(ValueError, match="readonly must be True"):
        digest.StrategyCategoryResearchCapacityRotationDigestConfig(readonly=False)


def test_generated_at_is_normalized_to_utc_and_rejects_naive_datetime() -> None:
    digest = api()

    class MissingOffsetTz(tzinfo):
        def utcoffset(self, dt):  # type: ignore[no-untyped-def]
            return None

        def dst(self, dt):  # type: ignore[no-untyped-def]
            return None

    digest_report = digest.build_strategy_category_research_capacity_rotation_digest(
        (),
        config=digest.StrategyCategoryResearchCapacityRotationDigestConfig(),
        generated_at=datetime(2026, 7, 2, 9, 0, tzinfo=timezone.utc),
    )

    assert digest_report.generated_at == datetime(2026, 7, 2, 9, 0, tzinfo=UTC)

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        digest.build_strategy_category_research_capacity_rotation_digest(
            (),
            config=digest.StrategyCategoryResearchCapacityRotationDigestConfig(),
            generated_at=datetime(2026, 7, 2, 9, 0),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        digest.build_strategy_category_research_capacity_rotation_digest(
            (),
            config=digest.StrategyCategoryResearchCapacityRotationDigestConfig(),
            generated_at=datetime(2026, 7, 2, 9, 0, tzinfo=MissingOffsetTz()),
        )


def test_digest_order_and_payload_are_input_order_deterministic() -> None:
    first = report(
        signal(
            "z-category",
            "z-strategy",
            queue_count="4",
            available_analyst_agent_slots="0",
        ),
        signal(
            "a-category",
            "a-strategy",
            queue_count="1",
            available_analyst_agent_slots="4",
        ),
    )
    second = report(
        signal(
            "a-category",
            "a-strategy",
            queue_count="1",
            available_analyst_agent_slots="4",
        ),
        signal(
            "z-category",
            "z-strategy",
            queue_count="4",
            available_analyst_agent_slots="0",
        ),
    )

    assert first.digest_rows == second.digest_rows
    assert api().strategy_category_research_capacity_rotation_digest_payload(
        first,
    ) == api().strategy_category_research_capacity_rotation_digest_payload(second)


def test_rows_and_reports_carry_tamper_evident_validation_digests() -> None:
    digest_report = report(
        signal(
            "crypto",
            "btc-capacity",
            rotation_status="rotating_in",
            liquidity_share_ratio_delta="0.100000",
            ending_liquidity_share_ratio="0.300000",
            queue_count="4",
            available_analyst_agent_slots="2",
        ),
    )
    row = digest_report.digest_rows[0]

    assert len(row.derived_validation_digest) == 64
    assert len(digest_report.derived_validation_digest) == 64

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(row, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(digest_report, derived_validation_digest="0" * 64)


def test_payload_revalidates_tampered_public_dataclasses_before_serializing() -> None:
    digest = api()

    tampered_row_report = report(
        signal(
            "crypto",
            "eth-capacity",
            queue_count="3",
            available_analyst_agent_slots="3",
        ),
    )
    object.__setattr__(
        tampered_row_report.digest_rows[0],
        "capacity_pressure_ratio",
        d("9.000000"),
    )
    with pytest.raises(ValueError, match="capacity_pressure_ratio"):
        digest.strategy_category_research_capacity_rotation_digest_payload(
            tampered_row_report,
        )

    tampered_report = report(signal("macro", "rates"))
    object.__setattr__(tampered_report, "pass_row_count", d("0"))
    with pytest.raises(ValueError, match="pass_row_count"):
        digest.strategy_category_research_capacity_rotation_digest_payload(
            tampered_report,
        )


def test_public_payload_rejects_missing_or_tampered_validation_digest() -> None:
    digest = api()
    payload = digest.strategy_category_research_capacity_rotation_digest_payload(
        report(signal("macro", "rates")),
    )

    assert len(payload["derived_validation_digest"]) == 64
    assert len(payload["digest_rows"][0]["derived_validation_digest"]) == 64

    missing_report_digest = dict(payload)
    del missing_report_digest["derived_validation_digest"]
    with pytest.raises(ValueError, match="derived_validation_digest"):
        digest.strategy_category_research_capacity_rotation_digest_payload(
            missing_report_digest,
        )

    missing_row_digest = {
        **payload,
        "digest_rows": (
            {
                key: value
                for key, value in payload["digest_rows"][0].items()
                if key != "derived_validation_digest"
            },
        ),
    }
    with pytest.raises(ValueError, match="derived_validation_digest"):
        digest.strategy_category_research_capacity_rotation_digest_payload(
            missing_row_digest,
        )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        digest.strategy_category_research_capacity_rotation_digest_payload(
            {**payload, "derived_validation_digest": "0" * 64},
        )


def test_module_scope_is_pure_in_memory_report_reducer_with_local_exports_only() -> None:
    digest = api()
    source = inspect.getsource(digest)
    tree = ast.parse(source)

    assert digest.__all__ == (
        "DEFAULT_STRATEGY_CATEGORY_RESEARCH_CAPACITY_ROTATION_DIGEST_CONFIG_VERSION",
        "ROTATION_STATUSES",
        "DIGEST_STATUSES",
        "StrategyCategoryResearchCapacityRotationDigestConfig",
        "StrategyCategoryResearchCapacityRotationSignal",
        "StrategyCategoryResearchCapacityRotationRow",
        "StrategyCategoryResearchCapacityRotationDigestReport",
        "build_strategy_category_research_capacity_rotation_digest",
        "strategy_category_research_capacity_rotation_digest_payload",
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
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "typing",
        "polymarket_alpha_lab",
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
        "fast",
        "live",
        "auth",
        "private_key",
        "api_key",
        "secret",
        "wallet",
        "account",
        "cancel",
        "replace",
        "order",
        "broker",
        "signing",
        "trade",
        "trading",
        "client",
        "execute",
        "connect",
        "subprocess",
        "open(",
        "pathlib",
    )
    assert all(term not in source.lower() for term in forbidden_source_terms)

    forbidden_call_names = {
        "__import__",
        "connect",
        "execute",
        "float",
        "open",
        "request",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names
