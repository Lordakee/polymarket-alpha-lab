import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 3, 13, 30, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def digest():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_policy_debate_momentum_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str = "source-alpha",
    *,
    event_key: str = "us-presidential-debate-alpha-winner",
    debate_id: str = "general-election-debate-alpha",
    candidate_id: str = "candidate-alpha",
    policy_topic: str = "healthcare",
    pre_debate_support_share: str | Decimal = "0.500000",
    post_debate_support_share: str | Decimal = "0.505000",
    mention_velocity_delta: str | Decimal = "0.020000",
    sentiment_delta: str | Decimal = "0.010000",
    hours_since_debate: str | Decimal = "72.000000",
    evidence_confidence: str | Decimal = "0.800000",
    observed_at: datetime = datetime(2026, 7, 3, 12, 0, tzinfo=UTC),
    upstream_reason_codes: tuple[str, ...] = (),
):
    module = digest()
    return module.PolicyDebateMomentumObservation(
        source_id=source_id,
        event_key=event_key,
        debate_id=debate_id,
        candidate_id=candidate_id,
        policy_topic=policy_topic,
        pre_debate_support_share=(
            pre_debate_support_share
            if isinstance(pre_debate_support_share, Decimal)
            else d(pre_debate_support_share)
        ),
        post_debate_support_share=(
            post_debate_support_share
            if isinstance(post_debate_support_share, Decimal)
            else d(post_debate_support_share)
        ),
        mention_velocity_delta=(
            mention_velocity_delta
            if isinstance(mention_velocity_delta, Decimal)
            else d(mention_velocity_delta)
        ),
        sentiment_delta=(
            sentiment_delta if isinstance(sentiment_delta, Decimal) else d(sentiment_delta)
        ),
        hours_since_debate=(
            hours_since_debate
            if isinstance(hours_since_debate, Decimal)
            else d(hours_since_debate)
        ),
        evidence_confidence=(
            evidence_confidence
            if isinstance(evidence_confidence, Decimal)
            else d(evidence_confidence)
        ),
        observed_at=observed_at,
        upstream_reason_codes=upstream_reason_codes,
    )


def report(*rows: object, cfg: object | None = None):
    module = digest()
    return module.build_market_research_policy_debate_momentum_digest(
        rows,
        config=cfg or module.PolicyDebateMomentumDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    module = digest()

    digest_report = report()

    assert isinstance(digest_report, module.PolicyDebateMomentumDigestReport)
    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-policy-debate-momentum-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_policy_debate_momentum_screening"
    )
    assert digest_report.input_count == d("0.000000")
    assert digest_report.row_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.stale_source_count == d("0.000000")
    assert digest_report.positive_momentum_count == d("0.000000")
    assert digest_report.negative_momentum_count == d("0.000000")
    assert digest_report.material_support_move_count == d("0.000000")
    assert digest_report.mention_velocity_shift_count == d("0.000000")
    assert digest_report.sentiment_shift_count == d("0.000000")
    assert digest_report.fresh_debate_window_count == d("0.000000")
    assert digest_report.max_policy_debate_momentum_score == d("0.000000")
    assert digest_report.average_policy_debate_momentum_score == d("0.000000")
    assert digest_report.max_absolute_support_move_share == d("0.000000")
    assert digest_report.average_absolute_support_move_share == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == ("policy_debate_momentum_digest_empty",)
    assert digest_report.reason_code_counts == (
        module.PolicyDebateMomentumReasonCodeCount(
            reason_code="policy_debate_momentum_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_high_risk_debate_momentum_blocks_probability_event_screening() -> None:
    digest_report = report(
        observation(
            "source-high",
            pre_debate_support_share="0.410000",
            post_debate_support_share="0.500000",
            mention_velocity_delta="0.700000",
            sentiment_delta="0.450000",
            hours_since_debate="12.000000",
            evidence_confidence="0.920000",
        ),
        observation(
            "source-watch",
            event_key="us-presidential-debate-beta-winner",
            debate_id="general-election-debate-beta",
            candidate_id="candidate-beta",
            policy_topic="immigration",
            pre_debate_support_share="0.500000",
            post_debate_support_share="0.540000",
            mention_velocity_delta="0.250000",
            sentiment_delta="0.100000",
            hours_since_debate="36.000000",
            observed_at=datetime(
                2026,
                7,
                3,
                8,
                45,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        observation(
            "source-pass",
            event_key="us-presidential-debate-gamma-winner",
            debate_id="general-election-debate-gamma",
            candidate_id="candidate-gamma",
            policy_topic="taxes",
        ),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_policy_debate_momentum_screening"
    )
    assert digest_report.input_count == d("3.000000")
    assert digest_report.row_count == d("3.000000")
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.stale_source_count == d("0.000000")
    assert digest_report.positive_momentum_count == d("3.000000")
    assert digest_report.negative_momentum_count == d("0.000000")
    assert digest_report.material_support_move_count == d("2.000000")
    assert digest_report.mention_velocity_shift_count == d("2.000000")
    assert digest_report.sentiment_shift_count == d("1.000000")
    assert digest_report.fresh_debate_window_count == d("2.000000")
    assert digest_report.max_policy_debate_momentum_score == d("1.000000")
    assert digest_report.average_policy_debate_momentum_score == d("0.529047")
    assert digest_report.max_absolute_support_move_share == d("0.090000")
    assert digest_report.average_absolute_support_move_share == d("0.045000")
    assert digest_report.reason_codes == (
        "policy_debate_momentum_below_threshold",
        "policy_debate_momentum_blocked",
        "policy_debate_momentum_fresh_debate_window",
        "policy_debate_momentum_mention_velocity_high",
        "policy_debate_momentum_mention_velocity_shift",
        "policy_debate_momentum_sentiment_high",
        "policy_debate_momentum_sentiment_shift",
        "policy_debate_momentum_source_fresh",
        "policy_debate_momentum_support_move_high",
        "policy_debate_momentum_support_move_material",
        "policy_debate_momentum_watch",
    )
    assert tuple(row.event_key for row in digest_report.rows) == (
        "us-presidential-debate-alpha-winner",
        "us-presidential-debate-beta-winner",
        "us-presidential-debate-gamma-winner",
    )

    blocked, watch, passed = digest_report.rows
    assert blocked.momentum_status == "blocked"
    assert blocked.momentum_direction == "positive"
    assert blocked.support_delta_share == d("0.090000")
    assert blocked.absolute_support_move_share == d("0.090000")
    assert blocked.policy_debate_momentum_score == d("1.000000")
    assert blocked.source_age_seconds == d("5400.000000")
    assert blocked.observed_at == datetime(2026, 7, 3, 12, 0, tzinfo=UTC)
    assert blocked.reason_codes == (
        "policy_debate_momentum_blocked",
        "policy_debate_momentum_fresh_debate_window",
        "policy_debate_momentum_mention_velocity_high",
        "policy_debate_momentum_mention_velocity_shift",
        "policy_debate_momentum_sentiment_high",
        "policy_debate_momentum_sentiment_shift",
        "policy_debate_momentum_source_fresh",
        "policy_debate_momentum_support_move_high",
        "policy_debate_momentum_support_move_material",
    )
    assert blocked.capped_confidence == d("0.920000")
    assert watch.momentum_status == "watch"
    assert watch.policy_debate_momentum_score == d("0.539285")
    assert watch.source_age_seconds == d("2700.000000")
    assert watch.reason_codes == (
        "policy_debate_momentum_fresh_debate_window",
        "policy_debate_momentum_mention_velocity_shift",
        "policy_debate_momentum_source_fresh",
        "policy_debate_momentum_support_move_material",
        "policy_debate_momentum_watch",
    )
    assert passed.momentum_status == "pass"
    assert passed.policy_debate_momentum_score == d("0.047857")
    assert passed.confidence_cap == d("0.650000")
    assert passed.capped_confidence == d("0.650000")
    assert passed.reason_codes == (
        "policy_debate_momentum_below_threshold",
        "policy_debate_momentum_source_fresh",
    )


def test_rows_and_reason_codes_are_sorted_deterministically() -> None:
    first = observation(
        "source-watch-b",
        event_key="beta-watch",
        pre_debate_support_share="0.500000",
        post_debate_support_share="0.540000",
        mention_velocity_delta="0.250000",
        sentiment_delta="0.100000",
        hours_since_debate="36.000000",
    )
    second = observation(
        "source-blocked",
        event_key="alpha-blocked",
        pre_debate_support_share="0.410000",
        post_debate_support_share="0.500000",
        mention_velocity_delta="0.700000",
        sentiment_delta="0.450000",
        hours_since_debate="12.000000",
    )
    third = observation(
        "source-watch-a",
        event_key="alpha-watch",
        pre_debate_support_share="0.500000",
        post_debate_support_share="0.540000",
        mention_velocity_delta="0.250000",
        sentiment_delta="0.100000",
        hours_since_debate="36.000000",
    )

    forward = report(first, second, third)
    reverse = report(third, second, first)

    assert forward == reverse
    assert tuple(row.event_key for row in forward.rows) == (
        "alpha-blocked",
        "alpha-watch",
        "beta-watch",
    )
    for row in forward.rows:
        assert row.reason_codes == tuple(sorted(row.reason_codes))
    assert forward.reason_codes == tuple(sorted(forward.reason_codes))
    assert tuple(item.reason_code for item in forward.reason_code_counts) == (
        forward.reason_codes
    )
    with pytest.raises(ValueError, match="rows must be a tuple"):
        replace(forward, rows=list(forward.rows))
    with pytest.raises(ValueError, match="reason_code_counts must be a tuple"):
        replace(forward, reason_code_counts=list(forward.reason_code_counts))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        replace(forward, reason_codes=list(forward.reason_codes))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        replace(forward.rows[0], reason_codes=list(forward.rows[0].reason_codes))
    with pytest.raises(ValueError, match="upstream_reason_codes must be a tuple"):
        observation(upstream_reason_codes=["source-a"])  # type: ignore[arg-type]


def test_non_default_thresholds_can_downgrade_moderate_momentum_risk() -> None:
    module = digest()
    cfg = module.PolicyDebateMomentumDigestConfig(
        watch_policy_debate_momentum_score=d("0.600000"),
        blocked_policy_debate_momentum_score=d("0.900000"),
        material_support_move_share=d("0.060000"),
        high_support_move_share=d("0.120000"),
        material_mention_velocity_delta=d("0.400000"),
        high_mention_velocity_delta=d("0.900000"),
        material_sentiment_delta=d("0.250000"),
        high_sentiment_delta=d("0.700000"),
    )

    digest_report = report(
        observation(
            "source-moderate",
            pre_debate_support_share="0.500000",
            post_debate_support_share="0.540000",
            mention_velocity_delta="0.250000",
            sentiment_delta="0.100000",
            hours_since_debate="36.000000",
        ),
        cfg=cfg,
    )

    assert digest_report.digest_status == "pass"
    assert digest_report.recommended_next_step == (
        "allow_report_only_policy_debate_momentum_screening"
    )
    assert digest_report.rows[0].momentum_status == "pass"
    assert digest_report.rows[0].policy_debate_momentum_score == d("0.338492")
    assert digest_report.rows[0].reason_codes == (
        "policy_debate_momentum_below_threshold",
        "policy_debate_momentum_fresh_debate_window",
        "policy_debate_momentum_source_fresh",
    )
    assert digest_report.material_support_move_count == d("0.000000")
    assert digest_report.mention_velocity_shift_count == d("0.000000")
    assert digest_report.sentiment_shift_count == d("0.000000")


def test_validation_rejects_bad_inputs_and_inconsistent_public_records() -> None:
    module = digest()

    for class_name in (
        "PolicyDebateMomentumDigestConfig",
        "PolicyDebateMomentumObservation",
        "PolicyDebateMomentumDigestRow",
        "PolicyDebateMomentumReasonCodeCount",
        "PolicyDebateMomentumDigestReport",
    ):
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Bad{class_name}", (getattr(module, class_name),), {})

    with pytest.raises(
        ValueError,
        match="watch_policy_debate_momentum_score must use six-decimal precision",
    ):
        module.PolicyDebateMomentumDigestConfig(
            watch_policy_debate_momentum_score=d("0.35"),
        )
    with pytest.raises(
        ValueError,
        match="watch_policy_debate_momentum_score must be a Decimal",
    ):
        module.PolicyDebateMomentumDigestConfig(
            watch_policy_debate_momentum_score=_DecimalSubclass("0.350000"),
        )
    with pytest.raises(ValueError, match="pre_debate_support_share must be a Decimal"):
        observation(pre_debate_support_share=_DecimalSubclass("0.500000"))
    with pytest.raises(
        ValueError,
        match="pre_debate_support_share must use six-decimal precision",
    ):
        observation(pre_debate_support_share=d("0.5"))
    with pytest.raises(ValueError, match="post_debate_support_share must be between 0 and 1"):
        observation(post_debate_support_share="1.100000")
    with pytest.raises(ValueError, match="hours_since_debate must be nonnegative"):
        observation(hours_since_debate="-1.000000")
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 3, 12, 0))
    with pytest.raises(ValueError, match="upstream_reason_codes must be canonical"):
        observation(upstream_reason_codes=("source-b", "source-a"))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_policy_debate_momentum_digest(
            (),
            config=module.PolicyDebateMomentumDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 3, 13, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        report("not-an-observation")
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(observation("source-dupe"), observation("source-dupe"))
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        module.build_market_research_policy_debate_momentum_digest(
            (observation("source-future"),),
            config=module.PolicyDebateMomentumDigestConfig(),
            generated_at=datetime(2026, 7, 3, 10, 0, tzinfo=UTC),
        )
    with pytest.raises(
        ValueError,
        match="material_support_move_share must not exceed high_support_move_share",
    ):
        module.PolicyDebateMomentumDigestConfig(
            material_support_move_share=d("0.200000"),
            high_support_move_share=d("0.100000"),
        )

    valid_row = report(observation("source-valid")).rows[0]
    with pytest.raises(
        ValueError,
        match="policy_debate_momentum_score must be a Decimal",
    ):
        replace(valid_row, policy_debate_momentum_score=_DecimalSubclass("0.990000"))
    with pytest.raises(
        ValueError,
        match="policy_debate_momentum_score must use six-decimal precision",
    ):
        replace(valid_row, policy_debate_momentum_score=d("0.99"))
    with pytest.raises(
        ValueError,
        match="policy_debate_momentum_score must match row factors",
    ):
        replace(valid_row, policy_debate_momentum_score=d("0.990000"))
    with pytest.raises(ValueError, match="reason_codes must match row factors"):
        replace(
            valid_row,
            reason_codes=(
                "policy_debate_momentum_below_threshold",
                "policy_debate_momentum_source_fresh",
                "policy_debate_momentum_support_move_material",
            ),
        )

    multi_row_report = report(
        observation("source-a"),
        observation(
            "source-b",
            event_key="aaa-blocked",
            pre_debate_support_share="0.410000",
            post_debate_support_share="0.500000",
            mention_velocity_delta="0.700000",
            sentiment_delta="0.450000",
            hours_since_debate="12.000000",
        ),
    )
    with pytest.raises(ValueError, match="rows must be canonical"):
        replace(multi_row_report, rows=tuple(reversed(multi_row_report.rows)))
    with pytest.raises(ValueError, match="reason_codes must be canonical"):
        replace(
            multi_row_report,
            reason_codes=tuple(reversed(multi_row_report.reason_codes)),
        )
    with pytest.raises(ValueError, match="reason_code_counts must be a tuple"):
        replace(
            multi_row_report,
            reason_code_counts=list(multi_row_report.reason_code_counts),
        )

    frozen_observation = observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]


def test_hard_flags_are_enforced_on_config_observations_rows_and_report() -> None:
    module = digest()

    digest_report = report(observation("source-hard-flags"))
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in digest_report.rows)
    assert all(
        item.paper_only and item.report_only and item.readonly
        for item in digest_report.reason_code_counts
    )

    for flag_name in ("paper_only", "report_only", "readonly"):
        with pytest.raises(ValueError, match=f"config {flag_name} must be True"):
            module.PolicyDebateMomentumDigestConfig(**{flag_name: False})
        with pytest.raises(ValueError, match=f"observation {flag_name} must be True"):
            replace(observation(f"source-observation-{flag_name}"), **{flag_name: False})
        with pytest.raises(ValueError, match=f"row {flag_name} must be True"):
            replace(digest_report.rows[0], **{flag_name: False})
        with pytest.raises(
            ValueError,
            match=f"reason_code_count {flag_name} must be True",
        ):
            replace(digest_report.reason_code_counts[0], **{flag_name: False})
        with pytest.raises(ValueError, match=f"report {flag_name} must be True"):
            replace(digest_report, **{flag_name: False})
    with pytest.raises(ValueError, match="count must be positive"):
        module.PolicyDebateMomentumReasonCodeCount(
            reason_code="policy_debate_momentum_digest_empty",
            count=d("0.000000"),
            row_ratio=d("0.000000"),
        )


def test_payload_uses_string_numerics_and_module_has_no_durable_or_live_surfaces() -> None:
    module = digest()
    digest_report = report(observation("source-payload"))

    payload = module.market_research_policy_debate_momentum_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["pre_debate_support_share"] == "0.500000"
    assert payload["rows"][0]["observed_at"] == "2026-07-03T12:00:00+00:00"

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                assert "private_key" not in lowered
                assert "wallet" not in lowered
                assert "order" not in lowered
                assert "auth" not in lowered
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, Decimal | datetime | float)

    walk_payload(payload)

    for public_record in (
        module.PolicyDebateMomentumDigestConfig(),
        observation("source-dataclass"),
        digest_report.rows[0],
        digest_report.reason_code_counts[0],
        digest_report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        assert {"market_slug", "question", "payload_json"}.isdisjoint(
            {field.name for field in fields(public_record)},
        )
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if _is_public_numeric(field_value):
                assert type(field_value) is Decimal, field.name

    source = Path(
        "src/polymarket_alpha_lab/market_research_policy_debate_momentum_digest.py",
    ).read_text()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "sqlite",
        "pathlib",
        "os",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "private_key",
        "wallet",
        "urlopen",
        "connect(",
        "execute(",
        "live trading",
        "submit_order",
        "cancel_order",
        "replace_order",
        "exchange",
        "asdict",
        "market_slug",
        "question",
        "payload_json",
    ):
        assert forbidden not in source.lower()


def test_payload_recursively_revalidates_public_dataclasses() -> None:
    module = digest()
    digest_report = report(observation("source-payload-validation"))
    object.__setattr__(
        digest_report.rows[0],
        "observed_at",
        datetime(2026, 7, 3, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    with pytest.raises(ValueError, match="observed_at must be UTC at payload time"):
        module.market_research_policy_debate_momentum_digest_payload(digest_report)


def _is_public_numeric(value: object) -> bool:
    return isinstance(value, Decimal)
