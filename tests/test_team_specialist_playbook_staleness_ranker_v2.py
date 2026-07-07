from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "team_specialist_playbook_staleness_ranker_v2.py"
)
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_playbook_staleness_ranker_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def context(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "review_id": "phase1_specialist_staleness_review",
        "required_category_ids": (
            "macro_rates",
            "election_policy",
            "crypto_btc",
        ),
        "required_source_family_ids": (
            "official_release",
            "market_price",
            "expert_analysis",
            "historical_baseline",
        ),
        "required_resolution_rule_ids": (
            "official_release_rule",
            "market_close_rule",
        ),
    }
    values.update(overrides)
    return module.TeamSpecialistPlaybookStalenessRankerV2Context(**values)


def playbook(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "team_id": "macro_specialists",
        "specialist_id": "macro_calibration_lead",
        "playbook_id": "macro_cpi_fresh_playbook",
        "category_ids": ("macro_rates", "election_policy", "crypto_btc"),
        "source_family_ids": (
            "official_release",
            "market_price",
            "expert_analysis",
            "historical_baseline",
        ),
        "resolution_rule_ids": ("official_release_rule", "market_close_rule"),
        "last_used_at": GENERATED_AT - timedelta(days=5),
        "recent_miss_count": d("0"),
        "sample_size": d("40"),
    }
    values.update(overrides)
    return module.TeamSpecialistPlaybookStalenessRankerV2Playbook(**values)


def build_report(*items: object, **overrides: object) -> Any:
    module = api()
    review_context = overrides.pop("review_context", context())
    config = overrides.pop("config", None)
    generated_at = overrides.pop("generated_at", GENERATED_AT)
    use_default_items = overrides.pop("use_default_items", True)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    if not items and use_default_items:
        items = (
            playbook(
                team_id="stale_specialists",
                specialist_id="source_resolution_lead",
                playbook_id="stale_crypto_resolution_playbook",
                category_ids=("crypto_btc",),
                source_family_ids=("official_release",),
                resolution_rule_ids=(),
                last_used_at=GENERATED_AT - timedelta(days=120),
                recent_miss_count=d("5"),
                sample_size=d("4"),
            ),
            playbook(
                team_id="watch_specialists",
                specialist_id="macro_source_lead",
                playbook_id="watch_macro_release_playbook",
                category_ids=("macro_rates", "election_policy"),
                source_family_ids=("official_release", "market_price"),
                resolution_rule_ids=("official_release_rule",),
                last_used_at=GENERATED_AT - timedelta(days=45),
                recent_miss_count=d("2"),
                sample_size=d("12"),
            ),
            playbook(),
        )
    return module.build_team_specialist_playbook_staleness_ranker_v2_report(
        review_context=review_context,
        playbooks=items,
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


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def test_builds_ranked_decimal_staleness_report_and_public_payload() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.rank_status == "stale"
    assert report.review_id == "phase1_specialist_staleness_review"
    assert report.playbook_count == d("3")
    assert report.stale_count == d("1")
    assert report.watch_count == d("1")
    assert report.fresh_count == d("1")
    assert report.average_staleness_score == d("0.450463")
    assert report.top_staleness_score == d("0.892500")
    assert report.reason_codes == (
        "team_specialist_playbook_staleness_rank_stale_rows",
        "team_specialist_playbook_staleness_rank_watch_rows",
        "team_specialist_playbook_staleness_rank_fresh_rows",
    )

    rows = report.rows
    assert tuple(row.playbook_id for row in rows) == (
        "stale_crypto_resolution_playbook",
        "watch_macro_release_playbook",
        "macro_cpi_fresh_playbook",
    )
    assert tuple(row.rank for row in rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.staleness_status for row in rows) == ("stale", "watch", "fresh")
    assert tuple(row.staleness_score for row in rows) == (
        d("0.892500"),
        d("0.445000"),
        d("0.013889"),
    )
    assert rows[0].last_used_age_days == d("120.000000")
    assert rows[0].last_used_age_score == d("1.000000")
    assert rows[0].recent_miss_score == d("1.000000")
    assert rows[0].source_family_drift_score == d("0.750000")
    assert rows[0].resolution_rule_drift_score == d("1.000000")
    assert rows[0].category_coverage_gap_score == d("0.666667")
    assert rows[0].sample_size_gap_score == d("0.800000")
    assert rows[0].missing_source_family_count == d("3")
    assert rows[0].missing_resolution_rule_count == d("2")
    assert rows[0].missing_category_count == d("2")
    assert rows[0].reason_codes == (
        "team_specialist_playbook_staleness_last_used_age",
        "team_specialist_playbook_staleness_recent_misses",
        "team_specialist_playbook_staleness_source_family_drift",
        "team_specialist_playbook_staleness_resolution_rule_drift",
        "team_specialist_playbook_staleness_category_coverage_gap",
        "team_specialist_playbook_staleness_sample_size_thin",
        "team_specialist_playbook_staleness_stale",
    )

    payload = report.payload
    assert payload["playbook_count"] == "3"
    assert payload["average_staleness_score"] == "0.450463"
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["staleness_score"] == "0.892500"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert_no_float_values(payload)


def test_empty_rank_is_digest_backed_and_report_only() -> None:
    module = api()

    report = module.build_team_specialist_playbook_staleness_ranker_v2_report(
        review_context=context(),
        playbooks=(),
        generated_at=GENERATED_AT,
    )

    assert report.rank_status == "fresh"
    assert report.playbook_count == d("0")
    assert report.stale_count == d("0")
    assert report.watch_count == d("0")
    assert report.fresh_count == d("0")
    assert report.average_staleness_score == d("0.000000")
    assert report.top_staleness_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("team_specialist_playbook_staleness_rank_empty",)
    assert report.payload["derived_validation_digest"] == report.derived_validation_digest
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_input_order_does_not_change_digest_or_payload() -> None:
    left = build_report(
        playbook(
            playbook_id="same_playbook",
            category_ids=("macro_rates", "crypto_btc"),
            source_family_ids=("official_release", "expert_analysis"),
            resolution_rule_ids=("market_close_rule",),
        ),
        review_context=context(
            required_category_ids=("macro_rates", "election_policy", "crypto_btc"),
            required_source_family_ids=(
                "official_release",
                "market_price",
                "expert_analysis",
                "historical_baseline",
            ),
            required_resolution_rule_ids=(
                "official_release_rule",
                "market_close_rule",
            ),
        ),
        use_default_items=False,
    )
    right = build_report(
        playbook(
            playbook_id="same_playbook",
            category_ids=("crypto_btc", "macro_rates"),
            source_family_ids=("expert_analysis", "official_release"),
            resolution_rule_ids=("market_close_rule",),
        ),
        review_context=context(
            required_category_ids=("crypto_btc", "macro_rates", "election_policy"),
            required_source_family_ids=(
                "historical_baseline",
                "expert_analysis",
                "market_price",
                "official_release",
            ),
            required_resolution_rule_ids=(
                "market_close_rule",
                "official_release_rule",
            ),
        ),
        use_default_items=False,
    )

    assert left.rows[0].matched_category_ids == right.rows[0].matched_category_ids
    assert left.rows[0].matched_source_family_ids == right.rows[0].matched_source_family_ids
    assert left.payload == right.payload
    assert left.derived_validation_digest == right.derived_validation_digest


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.TeamSpecialistPlaybookStalenessRankerV2Config()
    review_context = context()
    sample = playbook()
    report = build_report(sample, review_context=review_context, use_default_items=False)
    row = report.rows[0]

    for item in (config, review_context, sample, row, report):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.readonly = False  # type: ignore[misc]
        assert_public_numeric_values_are_decimal(item)


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "recent_miss_count",
            _DecimalSubclass("1"),
            "recent_miss_count must be exactly Decimal",
        ),
        (
            "sample_size",
            Decimal("NaN"),
            "sample_size must be finite",
        ),
        (
            "sample_size",
            d("1.5"),
            "sample_size must be an integral Decimal",
        ),
        (
            "recent_miss_count",
            d("-1"),
            "recent_miss_count must be >= 0.000000",
        ),
    ),
)
def test_playbook_validation_rejects_non_decimal_and_out_of_range_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        playbook(**{field_name: bad_value})


def test_config_validation_rejects_bad_weights_thresholds_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="last_used_age_weight must be exactly Decimal"):
        module.TeamSpecialistPlaybookStalenessRankerV2Config(
            last_used_age_weight=0,
        )
    with pytest.raises(ValueError, match="staleness weights must sum to 1.000000"):
        module.TeamSpecialistPlaybookStalenessRankerV2Config(
            sample_size_weight=d("0.090000"),
        )
    with pytest.raises(ValueError, match="watch_score_floor must not exceed stale_score_floor"):
        module.TeamSpecialistPlaybookStalenessRankerV2Config(
            watch_score_floor=d("0.800000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistPlaybookStalenessRankerV2Config(paper_only=False)


def test_build_validation_rejects_wrong_types_dates_duplicates_and_disabled_flags() -> None:
    module = api()

    with pytest.raises(
        ValueError,
        match="review_context must be TeamSpecialistPlaybookStalenessRankerV2Context",
    ):
        module.build_team_specialist_playbook_staleness_ranker_v2_report(
            review_context=object(),
            playbooks=(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="playbooks must be a list or tuple"):
        module.build_team_specialist_playbook_staleness_ranker_v2_report(
            review_context=context(),
            playbooks=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(
        ValueError,
        match="playbooks must contain TeamSpecialistPlaybookStalenessRankerV2Playbook",
    ):
        module.build_team_specialist_playbook_staleness_ranker_v2_report(
            review_context=context(),
            playbooks=[object()],
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_team_specialist_playbook_staleness_ranker_v2_report(
            review_context=context(),
            playbooks=[playbook()],
            generated_at=datetime(2026, 7, 7),
        )
    with pytest.raises(ValueError, match="last_used_at must be on or before generated_at"):
        module.build_team_specialist_playbook_staleness_ranker_v2_report(
            review_context=context(),
            playbooks=[playbook(last_used_at=GENERATED_AT + timedelta(seconds=1))],
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="playbooks must have unique public keys"):
        module.build_team_specialist_playbook_staleness_ranker_v2_report(
            review_context=context(),
            playbooks=(playbook(), playbook()),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="required_category_ids must not be empty"):
        context(required_category_ids=())
    with pytest.raises(ValueError, match="readonly must be True"):
        playbook(readonly=False)


def test_derived_validation_digest_rejects_tampering() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, average_staleness_score=d("0.400000"))
    with pytest.raises(ValueError, match="derived_validation_digest must match row fields"):
        replace(report.rows[0], staleness_score=d("0.800000"))


def test_rejects_unsafe_public_keys_and_values() -> None:
    module = api()

    for unsafe_value in (
        "live_team",
        "auth_team",
        "wallet_team",
        "order_team",
        "network_team",
        "database_team",
        "persist_team",
        "signing_team",
        "mutation_team",
        "buy_team",
        "sell_team",
        "trade_team",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            playbook(team_id=unsafe_value)

    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"order_id": "redacted"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"safe_key": "network note"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        replace(build_report().rows[0], reason_codes=("trade",))


def test_report_revalidates_row_order_counts_and_reason_codes() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="rows must be sorted by staleness score and rank"):
        replace(
            report,
            rows=(report.rows[1], report.rows[0], report.rows[2]),
        )
    with pytest.raises(ValueError, match="status counts must match rows"):
        replace(report, stale_count=d("2"))
    with pytest.raises(ValueError, match="reason_codes must match rank_status"):
        replace(
            report,
            reason_codes=("team_specialist_playbook_staleness_rank_empty",),
        )


def test_public_surface_is_readonly_report_only_and_has_no_live_surface() -> None:
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

    module = api()
    assert module.__all__ == (
        "DEFAULT_TEAM_SPECIALIST_PLAYBOOK_STALENESS_RANKER_V2_CONFIG_VERSION",
        "TeamSpecialistPlaybookStalenessRankerV2Config",
        "TeamSpecialistPlaybookStalenessRankerV2Context",
        "TeamSpecialistPlaybookStalenessRankerV2Playbook",
        "TeamSpecialistPlaybookStalenessRankerV2Report",
        "TeamSpecialistPlaybookStalenessRankerV2Row",
        "build_team_specialist_playbook_staleness_ranker_v2_report",
        "team_specialist_playbook_staleness_ranker_v2_payload",
    )
