from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 2, 20, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 2, 19, 55, tzinfo=UTC)
ZERO = Decimal("0.000000")
FORBIDDEN_SURFACE_TERMS = (
    "trading",
    "auth",
    "wallet",
    "broker",
    "submit",
    "cancel",
    "signing",
    "account",
    "advice",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.paper_candidate_fee_sensitivity_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": module.DEFAULT_PAPER_CANDIDATE_FEE_SENSITIVITY_DIGEST_CONFIG_VERSION,
        "watch_net_edge_floor": d("0.020000"),
        "blocked_net_edge_floor": d("0.000000"),
        "watch_fee_drag_share": d("0.300000"),
        "blocked_fee_drag_share": d("0.600000"),
    }
    values.update(overrides)
    return module.PaperCandidateFeeSensitivityDigestConfig(**values)


def candidate(**overrides: object):
    module = api()
    values = {
        "candidate_reference": "public-alpha",
        "market_slug": "alpha-market",
        "observed_at": OBSERVED_AT,
        "base_edge": d("0.100000"),
        "fee_drag": d("0.020000"),
        "stress_fee_drag": d("0.030000"),
        "reason_codes": ("candidate_fee_input",),
    }
    values.update(overrides)
    return module.PaperCandidateFeeSensitivityDigestCandidate(**values)


def report(*candidates: object, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_paper_candidate_fee_sensitivity_digest(
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
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_digest_scores_clear_watch_and_blocked_fee_sensitivity() -> None:
    result = report(
        candidate(
            candidate_reference="clear-alpha",
            market_slug="gamma-clear",
            base_edge=d("0.120000"),
            fee_drag=d("0.020000"),
            stress_fee_drag=d("0.030000"),
        ),
        candidate(
            candidate_reference="watch-alpha",
            market_slug="beta-watch",
            base_edge=d("0.080000"),
            fee_drag=d("0.020000"),
            stress_fee_drag=d("0.040000"),
        ),
        candidate(
            candidate_reference="secret-wallet-token-alpha",
            market_slug="alpha-blocked",
            base_edge=d("0.050000"),
            fee_drag=d("0.030000"),
            stress_fee_drag=d("0.040000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "paper-candidate-fee-sensitivity-digest-v0"
    assert result.candidate_count == d("3")
    assert result.clear_count == d("1")
    assert result.watch_count == d("1")
    assert result.blocked_count == d("1")
    assert result.max_stress_fee_drag == d("0.040000")
    assert result.max_fee_drag_share == d("0.800000")
    assert result.min_stressed_net_edge == d("-0.020000")
    assert result.status == "blocked"
    assert result.reason_codes == (
        "fee_sensitivity_negative_stressed_edge",
        "fee_sensitivity_net_edge_below_watch",
        "fee_sensitivity_fee_drag_share_elevated",
        "fee_sensitivity_stress_drag_present",
        "fee_sensitivity_base_drag_present",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.status for row in result.rows) == ("blocked", "watch", "clear")
    blocked, watched, cleared = result.rows

    assert blocked.redacted_candidate_reference.startswith("candidate_ref_")
    assert "secret" not in blocked.redacted_candidate_reference
    assert "wallet" not in blocked.redacted_candidate_reference
    assert "token" not in blocked.redacted_candidate_reference
    assert blocked.market_slug == "alpha-blocked"
    assert blocked.incremental_fee_drag == d("0.010000")
    assert blocked.total_fee_drag == d("0.070000")
    assert blocked.stressed_net_edge == d("-0.020000")
    assert blocked.fee_drag_share == d("0.800000")
    assert blocked.reason_codes == (
        "candidate_fee_input",
        "fee_sensitivity_base_drag_present",
        "fee_sensitivity_fee_drag_share_elevated",
        "fee_sensitivity_negative_stressed_edge",
        "fee_sensitivity_stress_drag_present",
    )

    assert watched.status == "watch"
    assert watched.incremental_fee_drag == d("0.020000")
    assert watched.total_fee_drag == d("0.060000")
    assert watched.stressed_net_edge == d("0.020000")
    assert watched.fee_drag_share == d("0.500000")
    assert watched.reason_codes == (
        "candidate_fee_input",
        "fee_sensitivity_base_drag_present",
        "fee_sensitivity_fee_drag_share_elevated",
        "fee_sensitivity_net_edge_below_clear",
        "fee_sensitivity_stress_drag_present",
    )

    assert cleared.status == "clear"
    assert cleared.incremental_fee_drag == d("0.010000")
    assert cleared.total_fee_drag == d("0.050000")
    assert cleared.stressed_net_edge == d("0.070000")
    assert cleared.fee_drag_share == d("0.250000")
    assert cleared.reason_codes == (
        "candidate_fee_input",
        "fee_sensitivity_base_drag_present",
        "fee_sensitivity_clear",
        "fee_sensitivity_stress_drag_present",
    )


def test_empty_report_is_clear_zeroed_decimal_and_readonly() -> None:
    empty = report()

    assert empty.candidate_count == d("0")
    assert empty.clear_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.blocked_count == d("0")
    assert empty.max_stress_fee_drag == ZERO
    assert empty.max_fee_drag_share == ZERO
    assert empty.min_stressed_net_edge == ZERO
    assert empty.status == "clear"
    assert empty.reason_codes == ("fee_sensitivity_digest_empty",)
    assert empty.rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    populated = report(candidate())
    for value in (empty, *populated.rows, populated):
        for item in fields(value):
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            item_value = getattr(value, item.name)
            if item.name.endswith(("_count", "_edge", "_drag", "_share")):
                assert type(item_value) is Decimal


def test_clear_candidate_with_only_stress_drag_gets_clear_reason() -> None:
    result = report(
        candidate(
            fee_drag=d("0.000000"),
            stress_fee_drag=d("0.010000"),
        ),
    )

    assert result.status == "clear"
    assert result.reason_codes == (
        "fee_sensitivity_clear",
        "fee_sensitivity_stress_drag_present",
    )
    row = result.rows[0]
    assert row.status == "clear"
    assert row.reason_codes == (
        "candidate_fee_input",
        "fee_sensitivity_clear",
        "fee_sensitivity_stress_drag_present",
    )


def test_payload_redacts_references_uses_decimal_strings_and_no_floats() -> None:
    module = api()
    result = report(
        candidate(
            candidate_reference="secret-wallet-token-alpha",
            market_slug="payload-market",
            base_edge=d("0.050000"),
            fee_drag=d("0.030000"),
            stress_fee_drag=d("0.040000"),
        ),
        generated_at=datetime(2026, 7, 2, 13, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.paper_candidate_fee_sensitivity_digest_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()
    assert payload["generated_at"] == "2026-07-02T20:00:00+00:00"
    assert payload["candidate_count"] == "1"
    assert payload["max_stress_fee_drag"] == "0.040000"
    assert payload["max_fee_drag_share"] == "0.800000"
    assert payload["min_stressed_net_edge"] == "-0.020000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["observed_at"] == "2026-07-02T19:55:00+00:00"
    assert payload["rows"][0]["redacted_candidate_reference"].startswith(
        "candidate_ref_",
    )
    assert payload["rows"][0]["total_fee_drag"] == "0.070000"
    assert payload["rows"][0]["stressed_net_edge"] == "-0.020000"
    assert "secret-wallet" not in rendered
    assert "wallet" not in rendered
    assert "token" not in rendered
    assert_no_float_values(payload)


def test_sorting_is_deterministic_by_status_net_drag_and_market() -> None:
    result = report(
        candidate(
            candidate_reference="watch-zulu",
            market_slug="zulu",
            base_edge=d("0.080000"),
            fee_drag=d("0.020000"),
            stress_fee_drag=d("0.040000"),
        ),
        candidate(
            candidate_reference="blocked-low",
            market_slug="bravo",
            base_edge=d("0.040000"),
            fee_drag=d("0.020000"),
            stress_fee_drag=d("0.030000"),
        ),
        candidate(
            candidate_reference="blocked-high",
            market_slug="charlie",
            base_edge=d("0.030000"),
            fee_drag=d("0.030000"),
            stress_fee_drag=d("0.040000"),
        ),
        candidate(
            candidate_reference="watch-alpha",
            market_slug="alpha",
            base_edge=d("0.080000"),
            fee_drag=d("0.020000"),
            stress_fee_drag=d("0.040000"),
        ),
    )

    assert tuple(row.market_slug for row in result.rows) == (
        "charlie",
        "bravo",
        "alpha",
        "zulu",
    )
    assert tuple(row.stressed_net_edge for row in result.rows) == (
        d("-0.040000"),
        d("-0.010000"),
        d("0.020000"),
        d("0.020000"),
    )


def test_validation_rejects_bad_types_floats_flags_and_consistency() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_paper_candidate_fee_sensitivity_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at="bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        module.PaperCandidateFeeSensitivityDigestReport(
            generated_at=_DatetimeSubclass(2026, 7, 2, 20, 0, tzinfo=UTC),
            config_version="paper-candidate-fee-sensitivity-digest-v0",
            candidate_count=ZERO,
            clear_count=ZERO,
            watch_count=ZERO,
            blocked_count=ZERO,
            max_stress_fee_drag=ZERO,
            max_fee_drag_share=ZERO,
            min_stressed_net_edge=ZERO,
            status="clear",
            reason_codes=("fee_sensitivity_digest_empty",),
            rows=(),
        )
    with pytest.raises(ValueError, match="base_edge"):
        candidate(base_edge=0.1)
    with pytest.raises(ValueError, match="fee_drag"):
        candidate(fee_drag=_DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="stress_fee_drag"):
        candidate(stress_fee_drag=Decimal("NaN"))
    with pytest.raises(ValueError, match="observed_at"):
        candidate(observed_at=datetime(2026, 7, 2, 19, 55))
    with pytest.raises(ValueError, match="observed_at"):
        report(candidate(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="duplicate candidate_reference"):
        report(candidate(), candidate())
    with pytest.raises(ValueError, match="reason_codes"):
        candidate(reason_codes=("z_reason", "a_reason"))
    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(config(), report_only=False)
    with pytest.raises(ValueError, match="candidate_count"):
        replace(report(candidate(candidate_reference="row")), candidate_count=d("2"))

    frozen = candidate(candidate_reference="frozen")
    with pytest.raises(FrozenInstanceError):
        frozen.market_slug = "changed"  # type: ignore[misc]


def test_public_api_and_static_no_io_no_live_surface_scope() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_PAPER_CANDIDATE_FEE_SENSITIVITY_DIGEST_CONFIG_VERSION",
        "PaperCandidateFeeSensitivityDigestCandidate",
        "PaperCandidateFeeSensitivityDigestConfig",
        "PaperCandidateFeeSensitivityDigestReport",
        "PaperCandidateFeeSensitivityDigestRow",
        "build_paper_candidate_fee_sensitivity_digest",
        "paper_candidate_fee_sensitivity_digest_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    source_path = (
        Path(__file__).resolve().parents[1]
        / "src/polymarket_alpha_lab/paper_candidate_fee_sensitivity_digest.py"
    )
    source = source_path.read_text()
    lowered_source = source.lower()
    for term in FORBIDDEN_SURFACE_TERMS:
        assert term not in lowered_source
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if hasattr(exported, "__dataclass_fields__"):
            assert not any(
                term in field.name.lower()
                for field in fields(exported)
                for term in FORBIDDEN_SURFACE_TERMS
            )

    tree = ast.parse(source)
    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "http",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    forbidden_call_names = {
        "connect",
        "execute",
        "executemany",
        "open",
        "request",
        "post",
        "put",
        "patch",
        "read",
        "write",
    }
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in forbidden_call_names

    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
