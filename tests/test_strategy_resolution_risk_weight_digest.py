from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, replace
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
    / "strategy_resolution_risk_weight_digest.py"
)
GENERATED_AT = datetime(2026, 7, 3, 16, 0, tzinfo=timezone(timedelta(hours=2)))
OBSERVED_AT = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_resolution_risk_weight_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": "strategy-resolution-risk-weight-digest-test-v0",
        "max_acknowledgement_lag_seconds": d("21600.000000"),
        "max_settlement_delay_seconds": d("86400.000000"),
        "min_pass_resolution_weight": d("0.700000"),
        "min_watch_resolution_weight": d("0.400000"),
        "min_source_authority": d("0.600000"),
        "min_evidence_quorum": d("0.600000"),
        "max_rule_ambiguity": d("0.300000"),
        "max_dispute_pressure": d("0.400000"),
    }
    values.update(overrides)
    return module.StrategyResolutionRiskWeightDigestConfig(**values)


def candidate(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "strategy_id": "strategy_macro",
        "candidate_id": "candidate_macro",
        "market_slug": "fed-cut-july-2026",
        "source_reference": "official-resolution-source",
        "observed_at": OBSERVED_AT,
        "rule_ambiguity": d("0.100000"),
        "source_authority": d("0.900000"),
        "dispute_pressure": d("0.100000"),
        "evidence_quorum": d("0.900000"),
        "acknowledgement_lag_seconds": d("3600.000000"),
        "settlement_delay_seconds": d("7200.000000"),
        "base_strategy_weight": d("0.800000"),
    }
    values.update(overrides)
    return module.StrategyResolutionRiskWeightCandidate(**values)


def report(*, candidates=(), cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_resolution_risk_weight_digest(
        candidates,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def assert_decimal_public_numbers(value: object) -> None:
    for item in fields(value):
        if item.name in {"paper_only", "report_only", "readonly"}:
            continue
        item_value = getattr(value, item.name)
        if item.name.endswith(
            (
                "_count",
                "_ratio",
                "_weight",
                "_score",
                "_seconds",
                "_ambiguity",
                "_authority",
                "_pressure",
                "_quorum",
            ),
        ):
            assert type(item_value) is Decimal


def assert_sha256(value: object) -> None:
    assert type(value) is str
    assert len(value) == 64
    assert value == value.lower()
    int(value, 16)


def test_digest_weights_candidates_by_resolution_risk_with_stable_reasons() -> None:
    result = report(
        candidates=(
            candidate(
                strategy_id="macro",
                candidate_id="candidate_pass",
                market_slug="alpha",
                rule_ambiguity=d("0.100000"),
                source_authority=d("0.900000"),
                dispute_pressure=d("0.100000"),
                evidence_quorum=d("0.900000"),
                acknowledgement_lag_seconds=d("3600.000000"),
                settlement_delay_seconds=d("7200.000000"),
                base_strategy_weight=d("0.800000"),
            ),
            candidate(
                strategy_id="crypto",
                candidate_id="candidate_watch",
                market_slug="beta",
                source_reference="secret-wallet-token-source",
                rule_ambiguity=d("0.250000"),
                source_authority=d("0.650000"),
                dispute_pressure=d("0.350000"),
                evidence_quorum=d("0.650000"),
                acknowledgement_lag_seconds=d("28800.000000"),
                settlement_delay_seconds=d("72000.000000"),
                base_strategy_weight=d("0.700000"),
            ),
            candidate(
                strategy_id="sports",
                candidate_id="candidate_block",
                market_slug="gamma",
                rule_ambiguity=d("0.700000"),
                source_authority=d("0.300000"),
                dispute_pressure=d("0.800000"),
                evidence_quorum=d("0.200000"),
                acknowledgement_lag_seconds=d("108000.000000"),
                settlement_delay_seconds=d("259200.000000"),
                base_strategy_weight=d("0.600000"),
            ),
        ),
    )

    assert result.generated_at == datetime(2026, 7, 3, 14, 0, tzinfo=UTC)
    assert result.config_version == "strategy-resolution-risk-weight-digest-test-v0"
    assert result.candidate_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.total_base_strategy_weight == d("2.100000")
    assert result.total_resolution_risk_weight == d("1.310883")
    assert result.average_resolution_quality_score == d("0.592000")
    assert result.status == "blocked"
    assert result.reason_codes == (
        "strategy_resolution_risk_weight_pass",
        "strategy_resolution_risk_weight_watch",
        "strategy_resolution_risk_weight_block",
        "rule_ambiguity_high",
        "source_authority_low",
        "dispute_pressure_high",
        "evidence_quorum_low",
        "acknowledgement_lag_high",
        "settlement_delay_high",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.candidate_id for row in result.rows) == (
        "candidate_pass",
        "candidate_watch",
        "candidate_block",
    )
    assert tuple(row.status for row in result.rows) == ("pass", "watch", "block")

    passed, watched, blocked = result.rows
    assert passed.resolution_quality_score == d("0.907500")
    assert passed.resolution_risk_weight == d("0.726000")
    assert passed.reason_codes == (
        "strategy_resolution_risk_weight_pass",
        "rule_ambiguity_contained",
        "source_authority_strong",
        "dispute_pressure_contained",
        "evidence_quorum_met",
        "acknowledgement_lag_contained",
        "settlement_delay_contained",
    )

    assert watched.redacted_source_reference.startswith("source_ref_")
    assert "secret" not in watched.redacted_source_reference
    assert "wallet" not in watched.redacted_source_reference
    assert "token" not in watched.redacted_source_reference
    assert watched.resolution_quality_score == d("0.637833")
    assert watched.resolution_risk_weight == d("0.446483")
    assert watched.reason_codes == (
        "strategy_resolution_risk_weight_watch",
        "rule_ambiguity_contained",
        "source_authority_strong",
        "dispute_pressure_contained",
        "evidence_quorum_met",
        "acknowledgement_lag_high",
        "settlement_delay_contained",
    )

    assert blocked.resolution_quality_score == d("0.230667")
    assert blocked.resolution_risk_weight == d("0.138400")
    assert blocked.reason_codes == (
        "strategy_resolution_risk_weight_block",
        "rule_ambiguity_high",
        "source_authority_low",
        "dispute_pressure_high",
        "evidence_quorum_low",
        "acknowledgement_lag_high",
        "settlement_delay_high",
    )


def test_empty_digest_is_watch_zeroed_decimal_and_report_only() -> None:
    empty = report()

    assert empty.candidate_count == d("0")
    assert empty.pass_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.block_count == d("0")
    assert empty.total_base_strategy_weight == d("0.000000")
    assert empty.total_resolution_risk_weight == d("0.000000")
    assert empty.average_resolution_quality_score == d("0.000000")
    assert empty.status == "watch"
    assert empty.reason_codes == ("strategy_resolution_risk_weight_digest_empty",)
    assert empty.reason_code_counts == ()
    assert empty.rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    populated = report(candidates=(candidate(),))
    for value in (empty, populated, *populated.rows, *populated.reason_code_counts):
        assert_decimal_public_numbers(value)


def test_rows_sort_by_status_weight_quality_and_identifiers() -> None:
    result = report(
        candidates=(
            candidate(
                strategy_id="z_strategy",
                candidate_id="z_pass",
                market_slug="zeta",
                base_strategy_weight=d("0.900000"),
            ),
            candidate(
                strategy_id="a_strategy",
                candidate_id="a_block",
                market_slug="alpha",
                rule_ambiguity=d("0.800000"),
                source_authority=d("0.200000"),
            ),
            candidate(
                strategy_id="b_strategy",
                candidate_id="b_watch",
                market_slug="beta",
                acknowledgement_lag_seconds=d("30000.000000"),
                base_strategy_weight=d("0.900000"),
            ),
            candidate(
                strategy_id="a_strategy",
                candidate_id="a_pass",
                market_slug="alpha",
                base_strategy_weight=d("0.900000"),
            ),
        ),
    )

    assert [
        (
            row.status,
            row.resolution_risk_weight,
            row.resolution_quality_score,
            row.strategy_id,
            row.candidate_id,
        )
        for row in result.rows
    ] == [
        ("pass", d("0.816750"), d("0.907500"), "a_strategy", "a_pass"),
        ("pass", d("0.816750"), d("0.907500"), "z_strategy", "z_pass"),
        ("watch", d("0.766650"), d("0.851833"), "b_strategy", "b_watch"),
        ("block", d("0.479600"), d("0.599500"), "a_strategy", "a_block"),
    ]


def test_reason_code_counts_are_deterministic_and_frequency_based() -> None:
    result = report(
        candidates=(
            candidate(
                candidate_id="one",
                rule_ambiguity=d("0.500000"),
                source_authority=d("0.200000"),
            ),
            candidate(
                candidate_id="two",
                rule_ambiguity=d("0.600000"),
                source_authority=d("0.300000"),
                evidence_quorum=d("0.100000"),
            ),
        ),
    )

    assert tuple(
        (count.reason_code, count.count)
        for count in result.reason_code_counts
    ) == (
        ("rule_ambiguity_high", d("2")),
        ("source_authority_low", d("2")),
        ("evidence_quorum_low", d("1")),
    )


def test_payload_redacts_references_uses_decimal_strings_and_no_floats() -> None:
    module = api()
    result = report(
        candidates=(
            candidate(
                source_reference="https://example.invalid/private?api_key=secret-token",
                acknowledgement_lag_seconds=d("28800.000000"),
            ),
        ),
        generated_at=datetime(2026, 7, 3, 7, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.strategy_resolution_risk_weight_digest_payload(result)
    rendered = repr(payload).lower()
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-03T14:00:00+00:00"
    assert payload["candidate_count"] == "1"
    assert payload["total_resolution_risk_weight"] == "0.682666"
    assert payload["average_resolution_quality_score"] == "0.853333"
    assert_sha256(payload["derived_validation_digest"])
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["rows"][0]["redacted_source_reference"].startswith("source_ref_")
    assert payload["rows"][0]["observed_at"] == "2026-07-03T12:00:00+00:00"
    assert_sha256(payload["rows"][0]["derived_validation_digest"])
    assert payload["rows"][0]["derived_validation_digest"] == result.rows[0].derived_validation_digest
    assert '"0.682666"' in encoded
    assert "api_key" not in rendered
    assert "secret" not in rendered
    assert "token" not in rendered
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)


def test_payload_revalidates_tamper_evident_derived_fields() -> None:
    module = api()
    result = report(candidates=(candidate(),))

    assert_sha256(result.rows[0].derived_validation_digest)
    assert_sha256(result.derived_validation_digest)

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(result.rows[0], derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(result, derived_validation_digest="0" * 64)

    tampered_row_report = report(candidates=(candidate(candidate_id="tampered-row"),))
    object.__setattr__(
        tampered_row_report.rows[0],
        "resolution_quality_score",
        d("0.123456"),
    )
    with pytest.raises(ValueError, match="resolution_risk_weight must match"):
        module.strategy_resolution_risk_weight_digest_payload(tampered_row_report)

    tampered_digest_report = report(candidates=(candidate(candidate_id="tampered-digest"),))
    object.__setattr__(tampered_digest_report, "pass_count", d("0"))
    with pytest.raises(ValueError, match="pass_count must match rows"):
        module.strategy_resolution_risk_weight_digest_payload(tampered_digest_report)


def test_payload_rejects_unsafe_public_values_after_tampering() -> None:
    module = api()
    result = report(candidates=(candidate(candidate_id="unsafe-public-value"),))
    object.__setattr__(result.rows[0], "market_slug", "wallet-order-cancel-market")

    with pytest.raises(ValueError, match="unsafe public value"):
        module.strategy_resolution_risk_weight_digest_payload(result)


def test_payload_redacts_live_surface_source_references() -> None:
    module = api()
    source_reference = (
        "https://example.invalid/api/v1/orders/cancel-replace"
        "?authorization=phase1-session"
    )

    result = report(candidates=(candidate(source_reference=source_reference),))
    payload = module.strategy_resolution_risk_weight_digest_payload(result)
    rendered = repr(payload).lower()

    assert payload["rows"][0]["redacted_source_reference"].startswith("source_ref_")
    assert "authorization" not in rendered
    assert "orders" not in rendered
    assert "cancel" not in rendered
    assert "replace" not in rendered
    assert "phase1-session" not in rendered


def test_payload_redacts_url_source_references_without_sensitive_tokens() -> None:
    module = api()

    result = report(
        candidates=(
            candidate(
                source_reference="https://example.invalid/public-resolution-source",
            ),
        ),
    )
    payload = module.strategy_resolution_risk_weight_digest_payload(result)
    rendered = repr(payload).lower()

    assert payload["rows"][0]["redacted_source_reference"].startswith("source_ref_")
    assert "https://" not in rendered
    assert "example.invalid" not in rendered
    assert "public-resolution-source" not in rendered


def test_public_identifier_strings_reject_sensitive_and_live_surface_text() -> None:
    with pytest.raises(ValueError, match="strategy_id must not expose unsafe public text"):
        candidate(strategy_id="secret-strategy")

    with pytest.raises(ValueError, match="candidate_id must not expose unsafe public text"):
        candidate(candidate_id="wallet-candidate")

    with pytest.raises(ValueError, match="market_slug must not expose unsafe public text"):
        candidate(market_slug="orders-cancel-replace")

    with pytest.raises(ValueError, match="config_version must not expose unsafe public text"):
        config(config_version="authorization-config")


def test_validation_rejects_bad_types_precision_duplicates_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_strategy_resolution_risk_weight_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="rule_ambiguity must be a Decimal"):
        candidate(rule_ambiguity=0.1)

    with pytest.raises(ValueError, match="source_authority must be finite"):
        candidate(source_authority=Decimal("NaN"))

    with pytest.raises(ValueError, match="observed_at must be exactly datetime"):
        candidate(observed_at=_DatetimeSubclass(2026, 7, 3, tzinfo=UTC))

    with pytest.raises(ValueError, match="base_strategy_weight must be a Decimal"):
        candidate(base_strategy_weight=_DecimalSubclass("0.500000"))

    with pytest.raises(ValueError, match="min_pass_resolution_weight"):
        config(min_pass_resolution_weight=d("0.200000"))

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(generated_at=datetime(2026, 7, 3, 14, 0))

    non_aware_tz = _NoneOffsetTimezone()
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(generated_at=datetime(2026, 7, 3, 14, 0, tzinfo=non_aware_tz))

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        candidate(observed_at=datetime(2026, 7, 3, 14, 0, tzinfo=non_aware_tz))

    with pytest.raises(ValueError, match="duplicate candidate_id"):
        report(
            candidates=(
                candidate(candidate_id="same", strategy_id="macro"),
                candidate(candidate_id="same", strategy_id="crypto"),
            ),
        )

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.StrategyResolutionRiskWeightDigestConfig(paper_only=False)

    row = report(candidates=(candidate(),)).rows[0]
    with pytest.raises(FrozenInstanceError):
        row.status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(row, readonly=False)


def test_payload_requires_report_type_and_hard_flags() -> None:
    module = api()
    result = report(candidates=(candidate(),))

    with pytest.raises(ValueError, match="report must be"):
        module.strategy_resolution_risk_weight_digest_payload(object())

    with pytest.raises(ValueError, match="report_only must be True"):
        module.strategy_resolution_risk_weight_digest_payload(
            replace(result, report_only=False),
        )


def test_module_scope_has_no_live_trading_persistence_network_or_sensitive_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    forbidden_import_fragments = (
        "api",
            "broker",
        "client",
        "db",
        "http",
        "network",
        "order",
        "psycopg",
        "request",
        "socket",
        "sql",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_names = {
        "open",
        "read",
        "write",
        "connect",
        "execute",
        "fetch",
        "request",
        "submit",
        "cancel",
        "sign",
        "trade",
    }
    forbidden_attr_fragments = (
        "account",
        "auth",
        "broker",
        "cancel",
        "client",
        "connect",
        "db",
        "execute",
        "fetch",
        "file",
        "network",
        "order",
        "persist",
        "request",
        "submit",
        "trade",
        "wallet",
        "write",
    )
    forbidden_attr_names = {
        "open",
        "read",
        "read_text",
        "read_bytes",
        "write",
        "write_text",
        "write_bytes",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert lowered not in forbidden_attr_names
            assert not any(
                fragment in lowered
                for fragment in forbidden_attr_fragments
                if fragment != "auth" or "authority" not in lowered
            )
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError(f"float literal leaked into reducer: {node.value!r}")

    assert imports
    for module_name in imports:
        assert not module_name.startswith("polymarket_alpha_lab.")
        lowered = module_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_import_fragments)
