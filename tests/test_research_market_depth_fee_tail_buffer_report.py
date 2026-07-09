from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, dataclass, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest


GENERATED_AT_EST = datetime(
    2026,
    7,
    9,
    9,
    30,
    tzinfo=timezone(timedelta(hours=-4)),
)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_depth_fee_tail_buffer_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate(
    candidate_ref: str,
    market_ref: str,
    market_label: str,
    evidence_ref: str,
    evidence_excerpt: str,
    *,
    available_depth_usd: str = "200.000000",
    required_tail_buffer_usd: str = "100.000000",
    fee_rate: str = "0.005000",
    tail_loss_rate: str = "0.050000",
    depth_staleness_seconds: str = "30",
    source_row_count: str = "1",
    source_missing: bool = False,
):
    module = api()
    return module.ResearchMarketDepthFeeTailBufferCandidate(
        candidate_ref=candidate_ref,
        market_ref=market_ref,
        market_label=market_label,
        evidence_ref=evidence_ref,
        evidence_excerpt=evidence_excerpt,
        observed_at=GENERATED_AT_EST,
        available_depth_usd=d(available_depth_usd),
        required_tail_buffer_usd=d(required_tail_buffer_usd),
        fee_rate=d(fee_rate),
        tail_loss_rate=d(tail_loss_rate),
        depth_staleness_seconds=d(depth_staleness_seconds),
        source_row_count=d(source_row_count),
        source_missing=source_missing,
    )


def report(*candidates):
    module = api()
    return module.build_research_market_depth_fee_tail_buffer_report(
        candidates,
        config=module.ResearchMarketDepthFeeTailBufferConfig(),
        generated_at=GENERATED_AT_EST,
    )


def fixture_candidates():
    return (
        candidate(
            "candidate-alpha-raw-id",
            "market-alpha-raw-id",
            "Will raw alpha question resolve yes?",
            "https://source.example/private-alpha?token=secret",
            "raw source text mentions wallet and live order details",
            available_depth_usd="80.000000",
            required_tail_buffer_usd="100.000000",
            fee_rate="0.060000",
            tail_loss_rate="0.350000",
            depth_staleness_seconds="120",
        ),
        candidate(
            "candidate-beta-raw-id",
            "market-beta-raw-id",
            "market beta private slug question",
            "postgres://private-dsn/table",
            "raw source text for beta",
            available_depth_usd="110.000000",
            required_tail_buffer_usd="100.000000",
            fee_rate="0.030000",
            tail_loss_rate="0.100000",
            depth_staleness_seconds="1000",
        ),
        candidate(
            "candidate-gamma-raw-id",
            "market-gamma-raw-id",
            "gamma private market label",
            "offline-private-gamma",
            "raw source text for gamma",
        ),
        candidate(
            "candidate-delta-raw-id",
            "market-delta-raw-id",
            "delta private missing source label",
            "offline-private-delta",
            "raw source text for delta",
            source_row_count="0",
            source_missing=True,
        ),
    )


def test_reduces_market_depth_fee_tail_buffer_candidates_to_deterministic_rows() -> None:
    buffer_report = report(*fixture_candidates())

    assert is_dataclass(buffer_report)
    assert buffer_report.generated_at == datetime(2026, 7, 9, 13, 30, tzinfo=UTC)
    assert (
        buffer_report.config_version
        == "research-market-depth-fee-tail-buffer-report-v1"
    )
    assert buffer_report.candidate_count == d("4")
    assert buffer_report.buffer_row_count == d("4")
    assert buffer_report.pass_row_count == d("1")
    assert buffer_report.watch_row_count == d("2")
    assert buffer_report.block_row_count == d("1")
    assert buffer_report.source_missing_count == d("1")
    assert buffer_report.report_status == "block"
    assert buffer_report.reason_codes == (
        "research_market_depth_fee_tail_buffer_block",
        "research_market_depth_fee_tail_buffer_source_missing",
    )
    assert buffer_report.paper_only is True
    assert buffer_report.report_only is True
    assert buffer_report.readonly is True

    blocked = buffer_report.buffer_rows[0]
    assert blocked.redacted_candidate_ref == "<redacted-candidate-001>"
    assert blocked.redacted_market_ref == "<redacted-market-001>"
    assert blocked.redacted_source_ref == "<redacted-source-001>"
    assert blocked.depth_buffer_ratio == d("0.800000")
    assert blocked.fee_tail_pressure == d("0.410000")
    assert blocked.buffer_status == "block"
    assert blocked.priority_rank == d("1")
    assert blocked.reason_codes == (
        "depth_buffer_below_required",
        "fee_rate_block",
        "tail_loss_block",
    )

    watched = buffer_report.buffer_rows[1]
    assert watched.depth_buffer_ratio == d("1.100000")
    assert watched.buffer_status == "watch"
    assert watched.reason_codes == (
        "depth_buffer_watch",
        "fee_rate_watch",
        "depth_snapshot_stale",
    )

    missing = buffer_report.buffer_rows[2]
    assert missing.buffer_status == "watch"
    assert missing.reason_codes == ("research_market_depth_fee_tail_buffer_source_missing",)

    clear = buffer_report.buffer_rows[3]
    assert clear.buffer_status == "pass"
    assert clear.reason_codes == ("market_depth_fee_tail_buffer_clear",)

    report_text = repr(buffer_report)
    for sensitive_token in (
        "candidate-alpha-raw-id",
        "market-alpha-raw-id",
        "Will raw alpha question resolve yes?",
        "https://source.example",
        "raw source text",
        "postgres://private-dsn/table",
    ):
        assert sensitive_token not in report_text


def test_empty_report_is_readonly_pass_with_decimal_zero_counts() -> None:
    buffer_report = report()

    assert buffer_report.candidate_count == d("0")
    assert buffer_report.buffer_row_count == d("0")
    assert buffer_report.pass_row_count == d("0")
    assert buffer_report.watch_row_count == d("0")
    assert buffer_report.block_row_count == d("0")
    assert buffer_report.source_missing_count == d("0")
    assert buffer_report.report_status == "pass"
    assert buffer_report.reason_codes == ("research_market_depth_fee_tail_buffer_clear",)
    assert buffer_report.buffer_rows == ()
    assert buffer_report.paper_only is True
    assert buffer_report.report_only is True
    assert buffer_report.readonly is True


def test_payload_is_json_ready_decimal_stringed_redacted_and_deterministic() -> None:
    module = api()
    first_report = report(*fixture_candidates())
    second_report = report(*reversed(fixture_candidates()))

    first_payload = module.research_market_depth_fee_tail_buffer_report_payload(first_report)
    second_payload = module.research_market_depth_fee_tail_buffer_report_payload(
        second_report,
    )
    payload_text = repr(first_payload).lower()

    for sensitive_token in (
        "candidate-alpha-raw-id",
        "market-alpha-raw-id",
        "raw alpha question",
        "source.example",
        "raw source text",
        "private-dsn",
        "wallet",
        "order",
    ):
        assert sensitive_token not in payload_text

    assert first_payload == second_payload
    assert json.dumps(first_payload, sort_keys=True, separators=(",", ":")) == json.dumps(
        second_payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    assert first_payload["candidate_count"] == "4"
    assert first_payload["buffer_rows"][0]["available_depth_usd"] == "80.000000"
    assert first_payload["buffer_rows"][0]["depth_buffer_ratio"] == "0.800000"
    assert first_payload["buffer_rows"][0]["validation_digest"].startswith("rmdftb-v1:")
    assert first_payload["validation_digest"] == first_report.validation_digest
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True


def test_payload_revalidates_sha256_digests_and_rejects_tampering() -> None:
    module = api()
    buffer_report = report(*fixture_candidates())
    row = buffer_report.buffer_rows[0]

    assert row.validation_digest.startswith("rmdftb-v1:")
    assert len(row.validation_digest.removeprefix("rmdftb-v1:")) == 64
    assert buffer_report.validation_digest.startswith("rmdftb-v1:")
    assert len(buffer_report.validation_digest.removeprefix("rmdftb-v1:")) == 64

    object.__setattr__(row, "fee_rate", d("0.010000"))
    with pytest.raises(ValueError, match="validation_digest|tamper"):
        module.research_market_depth_fee_tail_buffer_report_payload(buffer_report)

    count_tampered_report = report(candidate("safe-candidate", "safe-market", "safe label", "safe", "safe"))
    object.__setattr__(count_tampered_report, "pass_row_count", d("0"))
    with pytest.raises(ValueError, match="validation_digest|pass_row_count"):
        module.research_market_depth_fee_tail_buffer_report_payload(
            count_tampered_report,
        )


def test_payload_accepts_canonical_dicts_and_rejects_schema_or_numeric_drift() -> None:
    module = api()

    payload = module.research_market_depth_fee_tail_buffer_report_payload(
        report(candidate("safe-candidate", "safe-market", "safe label", "safe", "safe")),
    )

    assert module.research_market_depth_fee_tail_buffer_report_payload(payload) == payload

    incomplete_payload = dict(payload)
    incomplete_payload.pop("report_status")
    with pytest.raises(ValueError, match="schema|keys|required"):
        module.research_market_depth_fee_tail_buffer_report_payload(incomplete_payload)

    extra_payload = dict(payload)
    extra_payload["market_alias"] = "private-alpha"
    with pytest.raises(ValueError, match="schema|keys|unsafe"):
        module.research_market_depth_fee_tail_buffer_report_payload(extra_payload)

    tampered_payload = dict(payload)
    tampered_payload["candidate_count"] = "2"
    with pytest.raises(ValueError, match="validation_digest|candidate_count|buffer_row_count"):
        module.research_market_depth_fee_tail_buffer_report_payload(tampered_payload)

    with pytest.raises(ValueError, match="paper_only"):
        flag_payload = dict(payload)
        flag_payload["paper_only"] = False
        module.research_market_depth_fee_tail_buffer_report_payload(
            flag_payload,
        )

    with pytest.raises(ValueError, match="Decimal"):
        numeric_payload = dict(payload)
        numeric_payload["candidate_count"] = 1
        module.research_market_depth_fee_tail_buffer_report_payload(
            numeric_payload,
        )


def test_payload_rejects_nested_non_plain_payload_objects() -> None:
    module = api()

    class PayloadDict(dict):
        pass

    @dataclass(frozen=True)
    class ForeignPayload:
        note: str
        paper_only: bool = True
        report_only: bool = True
        readonly: bool = True

    for unsafe_payload in (
        {
            "nested": PayloadDict({"note": "safe"}),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "nested": ForeignPayload("safe"),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ):
        with pytest.raises(ValueError, match="unsafe payload object|plain"):
            module.research_market_depth_fee_tail_buffer_report_payload(unsafe_payload)


def test_public_dataclass_subclasses_are_rejected() -> None:
    module = api()

    @dataclass(frozen=True)
    class DerivedConfig(module.ResearchMarketDepthFeeTailBufferConfig):
        pass

    @dataclass(frozen=True)
    class DerivedCandidate(module.ResearchMarketDepthFeeTailBufferCandidate):
        pass

    with pytest.raises(ValueError, match="config"):
        DerivedConfig()

    with pytest.raises(ValueError, match="candidate"):
        DerivedCandidate(
            candidate_ref="safe-candidate",
            market_ref="safe-market",
            market_label="safe label",
            evidence_ref="safe",
            evidence_excerpt="safe",
            observed_at=GENERATED_AT_EST,
            available_depth_usd=d("1.000000"),
            required_tail_buffer_usd=d("1.000000"),
            fee_rate=d("0.000000"),
            tail_loss_rate=d("0.000000"),
            depth_staleness_seconds=d("0"),
        )


def test_payload_and_reason_codes_reject_unsafe_public_text() -> None:
    module = api()

    for payload in (
        {"candidate_id": "raw", "paper_only": True, "report_only": True, "readonly": True},
        {"candidate_ref": "raw", "paper_only": True, "report_only": True, "readonly": True},
        {"market_ref": "raw", "paper_only": True, "report_only": True, "readonly": True},
        {"market_label": "raw", "paper_only": True, "report_only": True, "readonly": True},
        {"market_slug": "raw", "paper_only": True, "report_only": True, "readonly": True},
        {"evidence_ref": "raw", "paper_only": True, "report_only": True, "readonly": True},
        {"evidence_excerpt": "raw", "paper_only": True, "report_only": True, "readonly": True},
        {"source_url": "https://example.invalid", "paper_only": True, "report_only": True, "readonly": True},
        {"note": "send a live trading order", "paper_only": True, "report_only": True, "readonly": True},
        {"dsn": "postgres://private", "paper_only": True, "report_only": True, "readonly": True},
    ):
        with pytest.raises(ValueError, match="unsafe|sensitive"):
            module.research_market_depth_fee_tail_buffer_report_payload(payload)

    row = report(candidate("safe-candidate", "safe-market", "safe label", "safe", "safe")).buffer_rows[0]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(row, reason_codes=("token_leak",))

    with pytest.raises(ValueError, match="redacted_candidate_ref must be redacted"):
        replace(row, redacted_candidate_ref="<redacted-candidate-secret>")


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    row = report(candidate("safe-candidate", "safe-market", "safe label", "safe", "safe")).buffer_rows[0]

    assert is_dataclass(row)
    with pytest.raises(FrozenInstanceError):
        row.fee_rate = d("0.010000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="readonly"):
        replace(row, readonly=False)

    with pytest.raises(ValueError, match="available_depth_usd must be a Decimal"):
        module.ResearchMarketDepthFeeTailBufferCandidate(
            candidate_ref="safe-candidate",
            market_ref="safe-market",
            market_label="safe label",
            evidence_ref="safe",
            evidence_excerpt="safe",
            observed_at=GENERATED_AT_EST,
            available_depth_usd=1,
            required_tail_buffer_usd=d("1.000000"),
            fee_rate=d("0.000000"),
            tail_loss_rate=d("0.000000"),
            depth_staleness_seconds=d("0"),
        )

    class DerivedDecimal(Decimal):
        pass

    with pytest.raises(ValueError, match="minimum_depth_buffer_ratio"):
        module.ResearchMarketDepthFeeTailBufferConfig(
            minimum_depth_buffer_ratio=DerivedDecimal("1.250000"),
        )

    with pytest.raises(ValueError, match="duplicate candidate"):
        report(
            candidate("safe-candidate", "safe-market-a", "safe label", "safe-a", "safe"),
            candidate("safe-candidate", "safe-market-b", "safe label", "safe-b", "safe"),
        )

    with pytest.raises(ValueError, match="report_only"):
        module.ResearchMarketDepthFeeTailBufferConfig(report_only=False)


def test_generated_at_and_observed_at_are_normalized_to_utc_and_reject_naive_datetime() -> None:
    module = api()

    class MissingOffsetTz(tzinfo):
        def utcoffset(self, dt):  # type: ignore[no-untyped-def]
            return None

        def dst(self, dt):  # type: ignore[no-untyped-def]
            return None

    buffer_report = module.build_research_market_depth_fee_tail_buffer_report(
        (
            module.ResearchMarketDepthFeeTailBufferCandidate(
                candidate_ref="safe-candidate",
                market_ref="safe-market",
                market_label="safe label",
                evidence_ref="safe",
                evidence_excerpt="safe",
                observed_at=GENERATED_AT_EST,
                available_depth_usd=d("1.000000"),
                required_tail_buffer_usd=d("1.000000"),
                fee_rate=d("0.000000"),
                tail_loss_rate=d("0.000000"),
                depth_staleness_seconds=d("0"),
            ),
        ),
        config=module.ResearchMarketDepthFeeTailBufferConfig(),
        generated_at=GENERATED_AT_EST,
    )

    assert buffer_report.generated_at == datetime(2026, 7, 9, 13, 30, tzinfo=UTC)
    assert buffer_report.buffer_rows[0].observed_at == datetime(2026, 7, 9, 13, 30, tzinfo=UTC)

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_market_depth_fee_tail_buffer_report(
            (),
            config=module.ResearchMarketDepthFeeTailBufferConfig(),
            generated_at=datetime(2026, 7, 9, 13, 30),
        )

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        module.ResearchMarketDepthFeeTailBufferCandidate(
            candidate_ref="safe-candidate",
            market_ref="safe-market",
            market_label="safe label",
            evidence_ref="safe",
            evidence_excerpt="safe",
            observed_at=datetime(2026, 7, 9, 13, 30, tzinfo=MissingOffsetTz()),
            available_depth_usd=d("1.000000"),
            required_tail_buffer_usd=d("1.000000"),
            fee_rate=d("0.000000"),
            tail_loss_rate=d("0.000000"),
            depth_staleness_seconds=d("0"),
        )


def test_module_scope_is_pure_in_memory_report_reducer_with_local_exports_only() -> None:
    module = api()
    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_MARKET_DEPTH_FEE_TAIL_BUFFER_CONFIG_VERSION",
        "DEPTH_FEE_TAIL_BUFFER_STATUSES",
        "ResearchMarketDepthFeeTailBufferConfig",
        "ResearchMarketDepthFeeTailBufferCandidate",
        "ResearchMarketDepthFeeTailBufferRow",
        "ResearchMarketDepthFeeTailBufferReport",
        "build_research_market_depth_fee_tail_buffer_report",
        "research_market_depth_fee_tail_buffer_report_payload",
    )
    assert module.DEPTH_FEE_TAIL_BUFFER_STATUSES == ("pass", "watch", "block")
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
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "sizing",
        "recommendation",
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
