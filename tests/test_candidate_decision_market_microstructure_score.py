import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_market_microstructure_score"
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        pytest.fail(f"missing market microstructure score module: {exc}")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_CANDIDATE_DECISION_MARKET_MICROSTRUCTURE_SCORE_CONFIG_VERSION
        ),
        "max_pass_spread": d("0.020000"),
        "max_watch_spread": d("0.050000"),
        "min_pass_depth_near_price": d("250.000000"),
        "min_watch_depth_near_price": d("50.000000"),
        "max_pass_book_age_seconds": d("30.000000"),
        "max_watch_book_age_seconds": d("120.000000"),
        "max_pass_price_impact": d("0.010000"),
        "max_watch_price_impact": d("0.030000"),
        "min_pass_liquidity_score": d("0.750000"),
        "min_watch_liquidity_score": d("0.400000"),
        "max_spread_for_score": d("0.100000"),
        "max_book_age_seconds_for_score": d("300.000000"),
        "max_price_impact_for_score": d("0.050000"),
    }
    values.update(overrides)
    return module.CandidateDecisionMarketMicrostructureScoreConfig(**values)


def candidate(**overrides: object):
    module = api()
    values = {
        "candidate_reference": "candidate-secret-token-alpha",
        "market_slug": "alpha-market",
        "side": "yes",
        "best_bid": d("0.490000"),
        "best_ask": d("0.500000"),
        "bid_depth_near_price": d("400.000000"),
        "ask_depth_near_price": d("500.000000"),
        "book_age_seconds": d("10.000000"),
        "paper_impact_notional": d("100.000000"),
    }
    values.update(overrides)
    return module.CandidateDecisionMarketMicrostructureCandidate(**values)


def report(*candidates: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_candidate_decision_market_microstructure_score(
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


def assert_sha256(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def test_tight_liquid_candidate_passes_with_microstructure_metrics() -> None:
    result = report(candidate())

    assert result.generated_at == GENERATED_AT
    assert result.config_version == "candidate-decision-market-microstructure-score-v0"
    assert result.candidate_count == d("1")
    assert result.pass_count == d("1")
    assert result.watch_count == d("0")
    assert result.blocked_count == d("0")
    assert result.min_liquidity_score == d("0.958333")
    assert result.max_spread == d("0.010000")
    assert result.max_book_age_seconds == d("10.000000")
    assert result.max_price_impact_estimate == ZERO
    assert result.status == "pass"
    assert result.reason_codes == ("market_microstructure_pass",)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_sha256(result.report_sha256)

    row = result.results[0]
    assert row.redacted_candidate_reference.startswith("candidate_ref_")
    assert "secret" not in row.redacted_candidate_reference
    assert "token" not in row.redacted_candidate_reference
    assert row.redacted_market_reference.startswith("market_ref_")
    assert row.redacted_market_reference != "alpha-market"
    assert row.side == "yes"
    assert row.side_bid_price == d("0.490000")
    assert row.side_ask_price == d("0.500000")
    assert row.spread == d("0.010000")
    assert row.midpoint_price == d("0.495000")
    assert row.executable_price == d("0.500000")
    assert row.depth_near_price == d("500.000000")
    assert row.crossed_book is False
    assert row.locked_book is False
    assert row.price_impact_estimate == ZERO
    assert row.liquidity_score == d("0.958333")
    assert row.status == "pass"
    assert row.reason_codes == ("market_microstructure_pass",)
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert_sha256(row.result_sha256)
    assert_sha256(row.derived_validation_digest)


def test_no_side_uses_inverse_midpoint_executable_and_bid_depth() -> None:
    row = report(
        candidate(
            candidate_reference="no-side-candidate",
            side="no",
            best_bid=d("0.410000"),
            best_ask=d("0.430000"),
            bid_depth_near_price=d("300.000000"),
            ask_depth_near_price=d("25.000000"),
        ),
    ).results[0]

    assert row.side == "no"
    assert row.side_bid_price == d("0.570000")
    assert row.side_ask_price == d("0.590000")
    assert row.spread == d("0.020000")
    assert row.midpoint_price == d("0.580000")
    assert row.executable_price == d("0.590000")
    assert row.depth_near_price == d("300.000000")
    assert row.status == "pass"


def test_wide_spread_watch_and_block_reason_codes() -> None:
    result = report(
        candidate(
            candidate_reference="wide-watch",
            market_slug="wide-watch-market",
            best_bid=d("0.500000"),
            best_ask=d("0.535000"),
        ),
        candidate(
            candidate_reference="wide-block",
            market_slug="wide-block-market",
            best_bid=d("0.500000"),
            best_ask=d("0.580000"),
        ),
    )

    assert result.status == "block"
    assert result.reason_codes == ("spread_block", "spread_watch")
    assert tuple(row.status for row in result.results) == ("block", "watch")
    blocked, watched = result.results
    assert blocked.redacted_market_reference.startswith("market_ref_")
    assert blocked.spread == d("0.080000")
    assert blocked.reason_codes == ("spread_block",)
    assert watched.redacted_market_reference.startswith("market_ref_")
    assert watched.spread == d("0.035000")
    assert watched.reason_codes == ("spread_watch",)


def test_stale_book_watch_and_block_reason_codes() -> None:
    result = report(
        candidate(
            candidate_reference="stale-watch",
            market_slug="stale-watch-market",
            book_age_seconds=d("75.000000"),
        ),
        candidate(
            candidate_reference="stale-block",
            market_slug="stale-block-market",
            book_age_seconds=d("150.000000"),
        ),
    )

    assert result.status == "block"
    assert result.reason_codes == ("book_stale_block", "book_stale_watch")
    assert tuple(row.status for row in result.results) == ("block", "watch")
    blocked, watched = result.results
    assert blocked.redacted_market_reference.startswith("market_ref_")
    assert blocked.reason_codes == ("book_stale_block",)
    assert watched.redacted_market_reference.startswith("market_ref_")
    assert watched.reason_codes == ("book_stale_watch",)


def test_crossed_book_blocks_and_locked_book_watches() -> None:
    result = report(
        candidate(
            candidate_reference="locked-book",
            market_slug="locked-market",
            best_bid=d("0.500000"),
            best_ask=d("0.500000"),
        ),
        candidate(
            candidate_reference="crossed-book",
            market_slug="crossed-market",
            best_bid=d("0.530000"),
            best_ask=d("0.520000"),
        ),
    )

    assert result.status == "block"
    assert result.reason_codes == ("crossed_book_block", "locked_book_watch")
    assert tuple(row.status for row in result.results) == ("block", "watch")
    crossed, locked = result.results
    assert crossed.redacted_market_reference.startswith("market_ref_")
    assert crossed.crossed_book is True
    assert crossed.locked_book is False
    assert crossed.spread == ZERO
    assert crossed.liquidity_score == ZERO
    assert crossed.reason_codes == ("crossed_book_block",)
    assert locked.redacted_market_reference.startswith("market_ref_")
    assert locked.crossed_book is False
    assert locked.locked_book is True
    assert locked.spread == ZERO
    assert locked.reason_codes == ("locked_book_watch",)


def test_combined_watch_conditions_can_block_on_liquidity_score() -> None:
    row = report(
        candidate(
            candidate_reference="aggregate-risk",
            market_slug="aggregate-risk-market",
            best_bid=d("0.500000"),
            best_ask=d("0.550000"),
            ask_depth_near_price=d("50.000000"),
            book_age_seconds=d("120.000000"),
            paper_impact_notional=d("125.000000"),
        ),
        cfg=config(min_watch_liquidity_score=d("0.500000")),
    ).results[0]

    assert row.liquidity_score == d("0.415000")
    assert row.status == "block"
    assert row.reason_codes == (
        "spread_watch",
        "depth_watch",
        "book_stale_watch",
        "price_impact_watch",
        "liquidity_score_block",
    )


def test_depth_and_price_impact_can_watch_or_block() -> None:
    result = report(
        candidate(
            candidate_reference="thin-watch",
            market_slug="thin-watch-market",
            ask_depth_near_price=d("150.000000"),
            paper_impact_notional=d("200.000000"),
        ),
        candidate(
            candidate_reference="thin-block",
            market_slug="thin-block-market",
            ask_depth_near_price=d("30.000000"),
        ),
    )

    assert result.status == "block"
    assert result.reason_codes == (
        "depth_block",
        "price_impact_block",
        "depth_watch",
        "price_impact_watch",
    )
    assert tuple(row.status for row in result.results) == ("block", "watch")
    blocked, watched = result.results
    assert blocked.depth_near_price == d("30.000000")
    assert blocked.price_impact_estimate == d("0.035000")
    assert blocked.reason_codes == ("depth_block", "price_impact_block")
    assert watched.depth_near_price == d("150.000000")
    assert watched.price_impact_estimate == d("0.012500")
    assert watched.reason_codes == ("depth_watch", "price_impact_watch")


def test_payload_redacts_references_uses_decimal_strings_and_validates_digests() -> None:
    module = api()
    result = report(
        candidate(candidate_reference="payload-secret-token"),
        generated_at=datetime(2026, 7, 7, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    assert module.validate_candidate_decision_market_microstructure_score_report(result) is True

    payload = module.candidate_decision_market_microstructure_score_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["candidate_count"] == "1.000000"
    assert payload["min_liquidity_score"] == "0.958333"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["results"][0]["redacted_candidate_reference"].startswith("candidate_ref_")
    assert payload["results"][0]["liquidity_score"] == "0.958333"
    assert_sha256(payload["results"][0]["derived_validation_digest"])
    assert payload["results"][0]["result_sha256"] == result.results[0].result_sha256
    assert_sha256(payload["derived_validation_digest"])
    assert payload["report_sha256"] == result.report_sha256
    assert "secret" not in rendered
    assert "token" not in rendered
    assert_no_float_values(payload)

    with pytest.raises(ValueError, match="liquidity_score must match"):
        replace(result.results[0], liquidity_score=d("0.123456"))
    with pytest.raises(ValueError, match="side_bid_price must match"):
        replace(result.results[0], side_bid_price=d("0.010000"))
    with pytest.raises(ValueError, match="result_sha256 must match"):
        replace(result.results[0], result_sha256="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(result.results[0], derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="min_liquidity_score must match"):
        replace(result, min_liquidity_score=d("0.123456"))
    with pytest.raises(ValueError, match="report_sha256 must match"):
        replace(result, report_sha256="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(result, derived_validation_digest="0" * 64)


def test_public_payload_redacts_market_reference_and_omits_position_sizing() -> None:
    module = api()
    raw_market_slug = "raw-market-slug-alpha"
    paper_notional = d("123.456789")
    result = report(
        candidate(
            candidate_reference="payload-redaction-candidate",
            market_slug=raw_market_slug,
            paper_impact_notional=paper_notional,
        ),
    )

    payload = module.candidate_decision_market_microstructure_score_payload(result)
    row_payload = payload["results"][0]
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True)

    assert row_payload["redacted_market_reference"].startswith("market_ref_")
    assert "market_slug" not in row_payload
    assert "paper_impact_notional" not in row_payload
    assert raw_market_slug not in rendered
    assert format(paper_notional, "f") not in rendered


def test_public_payload_validator_rejects_raw_reference_source_sizing_and_recommendation_surfaces() -> None:
    module = api()
    payload = module.candidate_decision_market_microstructure_score_payload(
        report(candidate(candidate_reference="public-validator-candidate")),
    )

    unsafe_payloads = (
        ({"candidate_id": "candidate-123"}, "unsafe public payload field"),
        ({"market_slug": "raw-market-slug"}, "unsafe public payload field"),
        ({"market_question": "Will this market resolve yes?"}, "unsafe public payload field"),
        ({"source_url": "https://example.test/source"}, "unsafe public payload field"),
        ({"dsn": "postgresql://example.test/db"}, "unsafe public payload field"),
        ({"table_name": "candidate_scores"}, "unsafe public payload field"),
        ({"paper_impact_notional": "100.000000"}, "unsafe public payload field"),
        ({"position_size": "10.000000"}, "unsafe public payload field"),
        ({"decision_label": "buy"}, "unsafe public payload value"),
        ({"review_note": "recommendation"}, "unsafe public payload value"),
    )
    for extra_payload, match in unsafe_payloads:
        with pytest.raises(ValueError, match=match):
            module.validate_candidate_decision_market_microstructure_score_public_payload(
                {**payload, **extra_payload},
            )


def test_empty_report_is_watch_zeroed_and_readonly() -> None:
    empty = report()

    assert empty.candidate_count == d("0")
    assert empty.pass_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.blocked_count == d("0")
    assert empty.min_liquidity_score == ZERO
    assert empty.max_spread == ZERO
    assert empty.max_book_age_seconds == ZERO
    assert empty.max_price_impact_estimate == ZERO
    assert empty.status == "watch"
    assert empty.reason_codes == ("market_microstructure_empty",)
    assert empty.results == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True
    assert_sha256(empty.report_sha256)


def test_results_are_deterministically_sorted_by_risk_then_market() -> None:
    result = report(
        candidate(candidate_reference="zeta-pass", market_slug="zeta-pass"),
        candidate(candidate_reference="alpha-pass", market_slug="alpha-pass"),
        candidate(
            candidate_reference="watch-risk",
            market_slug="watch-risk",
            best_bid=d("0.500000"),
            best_ask=d("0.535000"),
        ),
        candidate(
            candidate_reference="block-risk",
            market_slug="block-risk",
            book_age_seconds=d("150.000000"),
        ),
    )

    assert tuple(row.status for row in result.results) == (
        "block",
        "watch",
        "pass",
        "pass",
    )
    pass_market_references = tuple(
        row.redacted_market_reference for row in result.results[2:]
    )
    assert pass_market_references == tuple(sorted(pass_market_references))

    module = api()
    with pytest.raises(ValueError, match="results must be deterministically sorted"):
        module.CandidateDecisionMarketMicrostructureScoreReport(
            **{
                **result.__dict__,
                "results": tuple(reversed(result.results)),
            },
        )


def test_rejects_invalid_inputs_thresholds_duplicates_flags_and_unsafe_surface() -> None:
    module = api()
    valid_candidate = candidate(candidate_reference="valid-candidate")
    cfg = config()

    with pytest.raises(ValueError, match="candidates"):
        module.build_candidate_decision_market_microstructure_score(
            "not-candidates",
            config=cfg,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="CandidateDecisionMarketMicrostructureCandidate"):
        module.build_candidate_decision_market_microstructure_score(
            [object()],
            config=cfg,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        module.build_candidate_decision_market_microstructure_score(
            [valid_candidate],
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        module.build_candidate_decision_market_microstructure_score(
            [valid_candidate],
            config=cfg,
            generated_at=datetime(2026, 7, 7, 12, 0),
        )
    with pytest.raises(ValueError, match="duplicate candidate_reference"):
        report(valid_candidate, valid_candidate)
    with pytest.raises(ValueError, match="side"):
        candidate(side="maybe")
    with pytest.raises(ValueError, match="best_bid"):
        candidate(best_bid=d("-0.000001"))
    with pytest.raises(ValueError, match="best_ask"):
        candidate(best_ask=d("1.000001"))
    with pytest.raises(ValueError, match="best_bid"):
        candidate(best_bid=d("-0.0000004"))
    with pytest.raises(ValueError, match="best_ask"):
        candidate(best_ask=d("1.0000004"))
    with pytest.raises(ValueError, match="best_bid must be a Decimal"):
        candidate(best_bid=0.49)
    with pytest.raises(ValueError, match="exact Decimal"):
        candidate(best_bid=_DecimalSubclass("0.490000"))
    with pytest.raises(ValueError, match="finite"):
        candidate(book_age_seconds=Decimal("NaN"))
    with pytest.raises(ValueError, match="ask_depth_near_price"):
        candidate(ask_depth_near_price=d("-0.000001"))
    with pytest.raises(ValueError, match="paper_impact_notional"):
        candidate(paper_impact_notional=ZERO)
    with pytest.raises(ValueError, match="paper_only"):
        module.CandidateDecisionMarketMicrostructureCandidate(
            **{
                **valid_candidate.__dict__,
                "paper_only": False,
            },
        )
    with pytest.raises(ValueError, match="readonly"):
        module.CandidateDecisionMarketMicrostructureScoreConfig(
            **{
                **cfg.__dict__,
                "readonly": False,
            },
        )
    with pytest.raises(ValueError, match="max_pass_spread"):
        config(max_pass_spread=d("0.060000"))
    with pytest.raises(ValueError, match="min_pass_depth_near_price"):
        config(min_pass_depth_near_price=d("25.000000"))
    with pytest.raises(ValueError, match="max_pass_book_age_seconds"):
        config(max_pass_book_age_seconds=d("150.000000"))
    with pytest.raises(ValueError, match="min_pass_liquidity_score"):
        config(min_pass_liquidity_score=d("0.300000"))
    with pytest.raises(ValueError, match="datetime"):
        module.build_candidate_decision_market_microstructure_score(
            [candidate()],
            config=cfg,
            generated_at=_DatetimeSubclass(2026, 7, 7, 12, tzinfo=UTC),
        )

    payload = module.candidate_decision_market_microstructure_score_payload(report(valid_candidate))
    unsafe_payload = {
        **payload,
        "results": [
            {
                **payload["results"][0],
                "wallet": "must-not-be-public",
            },
        ],
    }
    with pytest.raises(ValueError, match="unsafe live surface field"):
        module.validate_candidate_decision_market_microstructure_score_public_payload(
            unsafe_payload,
        )
    unsafe_camel_case_payload = {
        **payload,
        "privateKey": "redacted",
    }
    with pytest.raises(ValueError, match="unsafe live surface field"):
        module.validate_candidate_decision_market_microstructure_score_public_payload(
            unsafe_camel_case_payload,
        )
    numeric_payload = {
        **payload,
        "diagnostic_count": 1,
    }
    with pytest.raises(ValueError, match="numeric public payload values"):
        module.validate_candidate_decision_market_microstructure_score_public_payload(
            numeric_payload,
        )
    with pytest.raises(ValueError, match="unsafe live surface value"):
        candidate(market_slug="contains-wallet")


def test_dataclasses_are_frozen_exact_decimal_only_and_hard_flagged() -> None:
    module = api()
    result = report(candidate())
    row = result.results[0]

    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]

    for klass in (
        module.CandidateDecisionMarketMicrostructureScoreConfig,
        module.CandidateDecisionMarketMicrostructureCandidate,
        module.CandidateDecisionMarketMicrostructureResult,
        module.CandidateDecisionMarketMicrostructureScoreReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    for value in (row, result):
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item.name.endswith(
                (
                    "_count",
            "_price",
            "_spread",
            "_depth",
            "_seconds",
            "_notional",
                    "_estimate",
                    "_score",
                ),
            ) or item.name in {"spread", "depth_near_price"}:
                assert type(item_value) is Decimal


def test_source_has_no_io_db_network_or_live_mutation_surface() -> None:
    module = api()
    source_path = Path(module.__file__)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)

    banned_import_roots = {
        "asyncio",
        "builtins.open",
        "csv",
        "http",
        "json",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    assert not (set(imports) & banned_import_roots)
    lowered = source.lower()
    for term in (
        "private_key",
        "wallet",
        "urlopen",
        "connect(",
        "execute(",
        "submit_",
        "cancel_",
        "replace",
        "exchange",
        "order",
        "target_notional",
    ):
        assert term not in lowered
