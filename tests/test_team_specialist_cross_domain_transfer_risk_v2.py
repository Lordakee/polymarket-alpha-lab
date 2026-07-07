from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "team_specialist_cross_domain_transfer_risk_v2.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_cross_domain_transfer_risk_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def transfer_risk(**overrides: object):
    module = api()
    values = {
        "team_id": "alpha_specialists",
        "specialist_id": "politics_mapper",
        "playbook_id": "election_news_reaction",
        "source_domain_id": "politics",
        "target_domain_id": "sports",
        "source_mismatch_score": d("0.900000"),
        "resolution_rule_mismatch_score": d("0.850000"),
        "volatility_regime_mismatch_score": d("0.800000"),
        "calibration_sample_count": d("3"),
        "last_calibrated_days_ago": d("90"),
    }
    values.update(overrides)
    return module.TeamSpecialistCrossDomainTransferRiskV2Input(**values)


def build_report(*items: object, **overrides: object):
    module = api()
    generated_at = overrides.pop(
        "generated_at",
        datetime(2026, 7, 6, 12, 0, tzinfo=UTC),
    )
    config = overrides.pop("config", None)
    use_default_items = overrides.pop("use_default_items", True)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    if not items and use_default_items:
        items = (
            transfer_risk(),
            transfer_risk(
                team_id="beta_specialists",
                specialist_id="crypto_mapper",
                playbook_id="liquidity_regime_mapping",
                source_domain_id="crypto",
                target_domain_id="macro",
                source_mismatch_score=d("0.500000"),
                resolution_rule_mismatch_score=d("0.350000"),
                volatility_regime_mismatch_score=d("0.700000"),
                calibration_sample_count=d("12"),
                last_calibrated_days_ago=d("30"),
            ),
            transfer_risk(
                team_id="gamma_specialists",
                specialist_id="macro_mapper",
                playbook_id="rates_resolution_mapping",
                source_domain_id="macro",
                target_domain_id="macro_policy",
                source_mismatch_score=d("0.100000"),
                resolution_rule_mismatch_score=d("0.050000"),
                volatility_regime_mismatch_score=d("0.150000"),
                calibration_sample_count=d("40"),
                last_calibrated_days_ago=d("5"),
            ),
        )
    return module.build_team_specialist_cross_domain_transfer_risk_v2(
        items,
        config=config,
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


def test_builds_cross_domain_transfer_risk_digest() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.transfer_risk_status == "high"
    assert report.candidate_count == d("3")
    assert report.low_risk_candidate_count == d("1")
    assert report.watch_risk_candidate_count == d("1")
    assert report.high_risk_candidate_count == d("1")
    assert report.average_transfer_risk_score == d("0.490556")
    assert report.top_transfer_risk_score == d("0.875000")
    assert report.bottom_transfer_risk_score == d("0.084167")
    assert report.reason_codes == (
        "cross_domain_transfer_risk_report_high_rows",
        "cross_domain_transfer_risk_report_watch_rows",
    )

    rows = report.rows
    assert tuple(row.team_id for row in rows) == (
        "alpha_specialists",
        "beta_specialists",
        "gamma_specialists",
    )
    assert tuple(row.rank for row in rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.transfer_risk_score for row in rows) == (
        d("0.875000"),
        d("0.512500"),
        d("0.084167"),
    )
    assert tuple(row.risk_band for row in rows) == ("high", "watch", "low")
    assert rows[0].calibration_sample_size_risk == d("0.850000")
    assert rows[0].recency_risk_score == d("1.000000")
    assert rows[1].calibration_sample_size_risk == d("0.400000")
    assert rows[1].recency_risk_score == d("0.666667")
    assert rows[2].calibration_sample_size_risk == d("0.000000")
    assert rows[2].recency_risk_score == d("0.111111")


def test_source_rule_volatility_sample_and_recency_reasons_are_deterministic() -> None:
    report = build_report()

    assert report.rows[0].reason_codes == (
        "cross_domain_transfer_risk_high",
        "source_mismatch_high",
        "resolution_rule_mismatch_high",
        "volatility_regime_mismatch_high",
        "calibration_sample_sparse",
        "recency_stale",
    )
    assert report.rows[1].reason_codes == (
        "cross_domain_transfer_risk_watch",
        "source_mismatch_watch",
        "resolution_rule_mismatch_low",
        "volatility_regime_mismatch_watch",
        "calibration_sample_partial",
        "recency_watch",
    )
    assert report.rows[2].reason_codes == (
        "cross_domain_transfer_risk_low",
        "source_mismatch_low",
        "resolution_rule_mismatch_low",
        "volatility_regime_mismatch_low",
        "calibration_sample_full",
        "recency_current",
    )


def test_payload_serializes_decimal_values_as_strings_and_is_readonly_report_only() -> None:
    report = build_report()
    payload = report.payload

    assert payload["candidate_count"] == "3"
    assert payload["average_transfer_risk_score"] == "0.490556"
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["transfer_risk_score"] == "0.875000"
    assert payload["rows"][0]["calibration_sample_size_risk"] == "0.850000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert_no_float_values(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_empty_report_is_digest_backed_and_hard_flagged() -> None:
    report = build_report(
        *(),
        generated_at=datetime(2026, 7, 6, 12, 0, tzinfo=UTC),
        use_default_items=False,
    )

    assert report.transfer_risk_status == "high"
    assert report.candidate_count == d("0")
    assert report.average_transfer_risk_score == d("0.000000")
    assert report.top_transfer_risk_score == d("0.000000")
    assert report.bottom_transfer_risk_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("cross_domain_transfer_risk_report_empty",)
    assert report.payload["derived_validation_digest"] == report.derived_validation_digest
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.TeamSpecialistCrossDomainTransferRiskV2Config()
    sample = transfer_risk()
    report = build_report(sample)
    row = report.rows[0]

    decimal_fields = {
        "source_mismatch_weight",
        "resolution_rule_mismatch_weight",
        "volatility_regime_mismatch_weight",
        "sample_size_risk_weight",
        "recency_risk_weight",
        "full_calibration_sample_count",
        "stale_recency_days",
        "high_risk_floor",
        "watch_risk_floor",
        "source_mismatch_score",
        "resolution_rule_mismatch_score",
        "volatility_regime_mismatch_score",
        "calibration_sample_count",
        "last_calibrated_days_ago",
        "rank",
        "calibration_sample_size_risk",
        "recency_risk_score",
        "transfer_risk_score",
        "candidate_count",
        "low_risk_candidate_count",
        "watch_risk_candidate_count",
        "high_risk_candidate_count",
        "average_transfer_risk_score",
        "top_transfer_risk_score",
        "bottom_transfer_risk_score",
    }

    for item in (config, sample, row, report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in decimal_fields:
                assert type(value) is Decimal


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "source_mismatch_score",
            _DecimalSubclass("0.900000"),
            "source_mismatch_score must be exactly Decimal",
        ),
        (
            "resolution_rule_mismatch_score",
            d("1.000001"),
            "resolution_rule_mismatch_score must be <= 1.000000",
        ),
        (
            "volatility_regime_mismatch_score",
            d("0.0500004"),
            "volatility_regime_mismatch_score must use six decimal places or fewer",
        ),
        (
            "last_calibrated_days_ago",
            Decimal("NaN"),
            "last_calibrated_days_ago must be finite",
        ),
        (
            "calibration_sample_count",
            d("1.5"),
            "calibration_sample_count must be an integral Decimal",
        ),
        (
            "last_calibrated_days_ago",
            d("-1"),
            "last_calibrated_days_ago must be >= 0.000000",
        ),
    ),
)
def test_input_validation_rejects_non_decimal_and_out_of_range_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        transfer_risk(**{field_name: bad_value})


def test_validation_rejects_bad_config_types_weights_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="source_mismatch_weight must be exactly Decimal"):
        module.TeamSpecialistCrossDomainTransferRiskV2Config(
            source_mismatch_weight=0,
        )
    with pytest.raises(ValueError, match="risk weights must sum to 1.000000"):
        module.TeamSpecialistCrossDomainTransferRiskV2Config(
            sample_size_risk_weight=d("0.160000"),
        )
    with pytest.raises(ValueError, match="watch_risk_floor must not exceed high_risk_floor"):
        module.TeamSpecialistCrossDomainTransferRiskV2Config(
            watch_risk_floor=d("0.900000"),
        )
    with pytest.raises(ValueError, match="full_calibration_sample_count must be positive"):
        module.TeamSpecialistCrossDomainTransferRiskV2Config(
            full_calibration_sample_count=d("0"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistCrossDomainTransferRiskV2Config(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        transfer_risk(readonly=False)


def test_build_validation_rejects_wrong_types_duplicates_and_bad_time() -> None:
    module = api()

    with pytest.raises(ValueError, match="transfer_risk_inputs must be an iterable"):
        module.build_team_specialist_cross_domain_transfer_risk_v2(
            object(),
            generated_at=datetime(2026, 7, 6, tzinfo=UTC),
        )
    with pytest.raises(
        ValueError,
        match="transfer risk items must be TeamSpecialistCrossDomainTransferRiskV2Input",
    ):
        module.build_team_specialist_cross_domain_transfer_risk_v2(
            [object()],
            generated_at=datetime(2026, 7, 6, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_team_specialist_cross_domain_transfer_risk_v2(
            [transfer_risk()],
            generated_at=datetime(2026, 7, 6),
        )
    duplicate = transfer_risk()
    with pytest.raises(ValueError, match="duplicate transfer risk keys"):
        build_report(duplicate, duplicate)


def test_derived_validation_digest_rejects_tampering() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(
            report,
            average_transfer_risk_score=d("0.500000"),
        )
    with pytest.raises(ValueError, match="reason_codes must match transfer_risk_status"):
        replace(
            report,
            reason_codes=("cross_domain_transfer_risk_report_low",),
        )


def test_report_revalidates_rows_sorting_counts_and_bands() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="rows must be sorted by risk score and rank"):
        replace(
            report,
            rows=(report.rows[1], report.rows[0], report.rows[2]),
        )
    with pytest.raises(ValueError, match="risk counts must match rows"):
        replace(
            report,
            high_risk_candidate_count=d("2"),
        )
    with pytest.raises(ValueError, match="risk_band must match transfer_risk_score"):
        replace(
            report.rows[0],
            risk_band="watch",
        )


def test_rejects_unsafe_public_keys_and_values() -> None:
    module = api()

    for unsafe_value in (
        "live_ref",
        "auth_ref",
        "wallet_ref",
        "order_ref",
        "network_ref",
        "database_ref",
        "persist_ref",
        "signing_ref",
        "mutation_ref",
        "buy_ref",
        "sell_ref",
        "trade_ref",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            transfer_risk(team_id=unsafe_value)

    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"wallet_ref": "redacted"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"safe_key": "network note"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"safe_key": 1})
    with pytest.raises(ValueError, match="unsafe public payload"):
        replace(build_report().rows[0], reason_codes=("trade",))


def test_module_scope_has_no_file_database_network_or_order_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "db",
        "http",
        "network",
        "pathlib",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "order",
        "persist",
        "place_order",
        "rollback",
        "sell",
        "send",
        "trade",
        "write",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert_no_float_values([imports, call_names, attribute_names])
