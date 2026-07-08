from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_crypto_event_signal_matrix import (
    DEFAULT_RESEARCH_CRYPTO_EVENT_SIGNAL_MATRIX_CONFIG_VERSION,
    CryptoEventSignalMatrixCandidate,
    CryptoEventSignalMatrixConfig,
    CryptoEventSignalMatrixReasonCodeCount,
    CryptoEventSignalMatrixReport,
    CryptoEventSignalMatrixRow,
    build_research_crypto_event_signal_matrix_report,
    research_crypto_event_signal_matrix_digest,
    research_crypto_event_signal_matrix_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path("src/polymarket_alpha_lab/research_crypto_event_signal_matrix.py")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> CryptoEventSignalMatrixConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_CRYPTO_EVENT_SIGNAL_MATRIX_CONFIG_VERSION,
        "event_relevance_watch": d("0.600000"),
        "event_relevance_block": d("0.850000"),
        "source_confidence_watch": d("0.500000"),
        "source_confidence_block": d("0.250000"),
        "contradiction_pressure_watch": d("0.350000"),
        "contradiction_pressure_block": d("0.700000"),
        "recency_watch_seconds": d("86400.000000"),
        "recency_block_seconds": d("259200.000000"),
    }
    values.update(overrides)
    return CryptoEventSignalMatrixConfig(**values)


def candidate(
    public_event_label: str = "bitcoin-etf-flow-window",
    *,
    asset_family: str = "bitcoin",
    event_family: str = "spot-etf-flow",
    event_relevance_score: Decimal = d("0.400000"),
    source_confidence_score: Decimal = d("0.900000"),
    contradiction_pressure_score: Decimal = d("0.100000"),
    recency_seconds: Decimal = d("3600.000000"),
    evidence_family_count: Decimal = d("3.000000"),
    reason_codes: tuple[str, ...] = ("crypto_event_signal_input_available",),
    observed_at: datetime = GENERATED_AT - timedelta(hours=1),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> CryptoEventSignalMatrixCandidate:
    return CryptoEventSignalMatrixCandidate(
        public_event_label=public_event_label,
        asset_family=asset_family,
        event_family=event_family,
        event_relevance_score=event_relevance_score,
        source_confidence_score=source_confidence_score,
        contradiction_pressure_score=contradiction_pressure_score,
        recency_seconds=recency_seconds,
        evidence_family_count=evidence_family_count,
        reason_codes=reason_codes,
        observed_at=observed_at,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: CryptoEventSignalMatrixCandidate,
    cfg: CryptoEventSignalMatrixConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> CryptoEventSignalMatrixReport:
    return build_research_crypto_event_signal_matrix_report(
        rows,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_no_float(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"found float in public payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float(item)


def test_pass_watch_block_rows_roll_up_to_public_report() -> None:
    digest = report(
        candidate("z-pass", event_relevance_score=d("0.300000")),
        candidate(
            "m-watch",
            event_relevance_score=d("0.700000"),
            source_confidence_score=d("0.600000"),
            contradiction_pressure_score=d("0.400000"),
            recency_seconds=d("90000.000000"),
        ),
        candidate(
            "a-block",
            event_relevance_score=d("0.900000"),
            source_confidence_score=d("0.200000"),
            contradiction_pressure_score=d("0.800000"),
        ),
    )

    assert digest.status == "block"
    assert digest.candidate_count == d("3.000000")
    assert digest.pass_count == d("1.000000")
    assert digest.watch_count == d("1.000000")
    assert digest.block_count == d("1.000000")
    assert tuple(row.public_event_label for row in digest.rows) == (
        "a-block",
        "m-watch",
        "z-pass",
    )
    assert digest.rows[0].public_status == "block"
    assert digest.rows[1].public_status == "watch"
    assert digest.rows[2].public_status == "pass"
    assert digest.reason_codes == (
        "crypto_event_signal_matrix_block",
        "contradiction_pressure_block",
        "event_relevance_block",
        "event_relevance_watch",
        "recency_watch",
        "source_confidence_block",
    )


def test_decimal_only_and_type_rejection() -> None:
    digest = report(candidate("decimal-only"))

    assert is_dataclass(CryptoEventSignalMatrixConfig)
    assert is_dataclass(CryptoEventSignalMatrixCandidate)
    assert is_dataclass(CryptoEventSignalMatrixRow)
    assert is_dataclass(CryptoEventSignalMatrixReasonCodeCount)
    assert is_dataclass(CryptoEventSignalMatrixReport)
    with pytest.raises(FrozenInstanceError):
        digest.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        digest.rows[0].priority_score = d("9.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="event_relevance_score"):
        candidate(event_relevance_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_confidence_score"):
        candidate(source_confidence_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="candidate_count"):
        replace(digest, candidate_count=1)  # type: ignore[arg-type]

    for item in (digest, *digest.rows, *digest.reason_code_counts):
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, bool):
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name


def test_public_leak_rejection_for_identifiers_sources_and_actions() -> None:
    forbidden_values = (
        "candidate_id_123",
        "market-id-123",
        "market_slug_btc",
        "will bitcoin break 100k question",
        "source_ref_internal",
        "https://example.test/source",
        "raw text excerpt",
        "postgres_dsn",
        "table_name",
        "api_token",
        "wallet-alpha",
        "order-field",
        "buy-recommendation",
        "sell-signal",
        "position-size",
    )
    for value in forbidden_values:
        with pytest.raises(ValueError, match="unsafe"):
            candidate(public_event_label=value)

    digest = report(candidate("safe-public-label"))
    object.__setattr__(digest.rows[0], "public_event_label", "wallet leak")
    with pytest.raises(ValueError, match="unsafe"):
        research_crypto_event_signal_matrix_payload(digest)


def test_hard_flags_are_required_on_every_public_surface() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        candidate(report_only=False)

    digest = report(candidate("flag-row"))
    with pytest.raises(ValueError, match="readonly"):
        replace(digest, readonly=False)
    object.__setattr__(digest.rows[0], "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        research_crypto_event_signal_matrix_payload(digest)


def test_deterministic_payload_and_digest_are_stable_and_consistent() -> None:
    inputs = (
        candidate("z-watch", event_relevance_score=d("0.700000")),
        candidate("a-pass", event_relevance_score=d("0.200000")),
    )
    first = report(*inputs)
    second = report(*reversed(inputs))

    first_payload = research_crypto_event_signal_matrix_payload(first)
    second_payload = research_crypto_event_signal_matrix_payload(second)
    assert first_payload == second_payload
    assert json.dumps(first_payload, sort_keys=True) == json.dumps(
        second_payload,
        sort_keys=True,
    )
    assert_no_float(first_payload)

    digest_payload = research_crypto_event_signal_matrix_digest(first)
    assert digest_payload == {
        "generated_at": GENERATED_AT.isoformat(),
        "config_version": DEFAULT_RESEARCH_CRYPTO_EVENT_SIGNAL_MATRIX_CONFIG_VERSION,
        "status": first_payload["status"],
        "candidate_count": first_payload["candidate_count"],
        "pass_count": first_payload["pass_count"],
        "watch_count": first_payload["watch_count"],
        "block_count": first_payload["block_count"],
        "reason_codes": first_payload["reason_codes"],
        "top_rows": first_payload["rows"][:3],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def test_empty_inputs_block_without_leaking_source_data() -> None:
    digest = report()

    assert digest.status == "block"
    assert digest.candidate_count == ZERO
    assert digest.reason_codes == ("crypto_event_signal_matrix_no_inputs",)
    assert digest.reason_code_counts == (
        CryptoEventSignalMatrixReasonCodeCount(
            reason_code="crypto_event_signal_matrix_no_inputs",
            count=d("1.000000"),
        ),
    )
    assert digest.rows == ()


def test_datetime_and_public_status_validation() -> None:
    with pytest.raises(ValueError, match="observed_at"):
        candidate(observed_at=datetime(2026, 7, 8, 11, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(candidate("time"), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        candidate(
            observed_at=datetime(2026, 7, 8, 11, 0, tzinfo=_NoneOffsetTimezone()),
        )

    digest = report(
        candidate(
            "offset-time",
            observed_at=datetime(2026, 7, 8, 7, 0, tzinfo=timezone(timedelta(hours=-4))),
        ),
    )
    assert digest.rows[0].observed_at == datetime(2026, 7, 8, 11, 0, tzinfo=UTC)

    with pytest.raises(ValueError, match="public_status"):
        CryptoEventSignalMatrixRow(
            public_event_label="bad-status",
            asset_family="bitcoin",
            event_family="spot-etf-flow",
            public_status="blocked",
            event_relevance_score=d("0.900000"),
            source_confidence_score=d("0.900000"),
            contradiction_pressure_score=d("0.100000"),
            recency_seconds=d("3600.000000"),
            evidence_family_count=d("3.000000"),
            priority_score=d("0.900000"),
            observed_at=GENERATED_AT,
            reason_codes=("crypto_event_signal_input_available",),
        )


def test_public_exports_and_static_forbidden_surface_are_exact() -> None:
    import polymarket_alpha_lab.research_crypto_event_signal_matrix as matrix

    assert matrix.__all__ == (
        "DEFAULT_RESEARCH_CRYPTO_EVENT_SIGNAL_MATRIX_CONFIG_VERSION",
        "CryptoEventSignalMatrixCandidate",
        "CryptoEventSignalMatrixConfig",
        "CryptoEventSignalMatrixReasonCodeCount",
        "CryptoEventSignalMatrixReport",
        "CryptoEventSignalMatrixRow",
        "build_research_crypto_event_signal_matrix_report",
        "research_crypto_event_signal_matrix_digest",
        "research_crypto_event_signal_matrix_payload",
    )

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live",
        "trading",
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "exchange",
        "private_key",
        "api_key",
        "secret",
        "position",
        "trade",
        "bet",
        "stake",
        "client",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__", "asdict"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
            assert all(alias.name != "asdict" for alias in node.names)
