from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, ROUND_DOWN, localcontext
import hashlib
import importlib
import json
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def m():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_market_depth_probability_memory_scorecard_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def config(**overrides: object):
    values = {
        "config_version": (
            "research-market-depth-probability-memory-scorecard-report-v0"
        ),
        "target_depth": d("1000.000000"),
        "min_source_count": d("3"),
        "pass_score_min": d("0.750000"),
        "watch_score_min": d("0.450000"),
        "stale_memory_age_seconds": d("86400"),
        "probability_memory_weight": d("0.400000"),
        "market_depth_weight": d("0.400000"),
        "source_diversity_weight": d("0.200000"),
    }
    values.update(overrides)
    return m().ResearchMarketDepthProbabilityMemoryScorecardConfig(**values)


def observation(
    index: int,
    *,
    candidate_id: str = "candidate://private-alpha?secret=abc",
    market_id: str = "market-question-text: Will alpha resolve yes?",
    source_reference: str = "https://vendor.example/source?secret=abc",
    probability: Decimal = d("0.620000"),
    previous_probability: Decimal = d("0.600000"),
    bid_depth: Decimal = d("600.000000"),
    ask_depth: Decimal = d("400.000000"),
    source_count: Decimal = d("2"),
    observed_at: datetime | None = None,
    reason_codes: tuple[str, ...] = (),
):
    return m().ResearchMarketDepthProbabilityMemoryScorecardObservation(
        candidate_id=f"{candidate_id}-{index}",
        market_id=market_id,
        source_reference=f"{source_reference}-{index}",
        probability=probability,
        previous_probability=previous_probability,
        bid_depth=bid_depth,
        ask_depth=ask_depth,
        source_count=source_count,
        observed_at=(
            observed_at if observed_at is not None else GENERATED_AT - timedelta(hours=1)
        ),
        reason_codes=reason_codes,
    )


def build_report(rows: tuple[object, ...], *, cfg: object | None = None):
    return m().build_research_market_depth_probability_memory_scorecard_report(
        rows,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def test_empty_input_returns_report_only_block_scorecard() -> None:
    report = build_report(())

    assert type(report) is m().ResearchMarketDepthProbabilityMemoryScorecardReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        "research-market-depth-probability-memory-scorecard-report-v0"
    )
    assert report.row_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.average_score is None
    assert report.status == "block"
    assert report.reason_codes == ("no_market_depth_probability_memory_inputs",)
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_builds_pass_watch_and_block_rows_with_decimal_only_scores() -> None:
    pass_candidate = "candidate://private-alpha?secret=abc"
    watch_candidate = "candidate://private-beta?secret=abc"
    block_candidate = "candidate://private-gamma?secret=abc"

    report = build_report(
        (
            observation(
                2,
                candidate_id=pass_candidate,
                probability=d("0.640000"),
                previous_probability=d("0.630000"),
                bid_depth=d("700.000000"),
                ask_depth=d("500.000000"),
                observed_at=GENERATED_AT - timedelta(minutes=30),
                reason_codes=("manual_reviewed",),
            ),
            observation(
                1,
                candidate_id=pass_candidate,
                probability=d("0.620000"),
                previous_probability=d("0.600000"),
            ),
            observation(
                1,
                candidate_id=watch_candidate,
                market_id="market-question-text: Will beta resolve yes?",
                probability=d("0.550000"),
                previous_probability=d("0.350000"),
                bid_depth=d("125.000000"),
                ask_depth=d("125.000000"),
                source_count=d("1"),
                observed_at=GENERATED_AT - timedelta(hours=2),
            ),
            observation(
                1,
                candidate_id=block_candidate,
                market_id="market-question-text: Will gamma resolve yes?",
                probability=d("0.900000"),
                previous_probability=d("0.100000"),
                bid_depth=d("25.000000"),
                ask_depth=d("25.000000"),
                source_count=d("0"),
                observed_at=GENERATED_AT - timedelta(hours=3),
            ),
        ),
    )

    rows_by_candidate = {row.candidate_digest: row for row in report.rows}
    pass_row = rows_by_candidate[digest(pass_candidate + "-1")]
    watch_row = rows_by_candidate[digest(watch_candidate + "-1")]
    block_row = rows_by_candidate[digest(block_candidate + "-1")]

    assert report.status == "block"
    assert report.row_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.average_score == d("0.526889")
    assert pass_row.status == "pass"
    assert pass_row.observation_count == d("2")
    assert pass_row.latest_memory_age_seconds == d("1800")
    assert pass_row.average_probability == d("0.630000")
    assert pass_row.average_probability_delta_abs == d("0.015000")
    assert pass_row.probability_memory_score == d("0.985000")
    assert pass_row.average_depth == d("1100.000000")
    assert pass_row.market_depth_score == d("1.000000")
    assert pass_row.source_diversity_score == d("1.000000")
    assert pass_row.score == d("0.994000")
    assert pass_row.reason_codes == (
        "input_manual_reviewed",
        "market_depth_probability_memory_pass",
        "probability_memory_stable",
        "sufficient_depth",
        "sufficient_source_count",
    )
    assert watch_row.status == "watch"
    assert watch_row.score == d("0.486667")
    assert block_row.status == "block"
    assert block_row.score == d("0.100000")
    assert all(isinstance(value, Decimal) for row in report.rows for value in row.decimals)


def test_stale_memory_age_boundary_is_blocking() -> None:
    report = build_report(
        (
            observation(
                1,
                bid_depth=d("700.000000"),
                ask_depth=d("500.000000"),
                source_count=d("3.000000"),
                observed_at=GENERATED_AT - timedelta(seconds=86400),
            ),
        ),
    )
    row = report.rows[0]

    assert row.score == d("0.992000")
    assert row.latest_memory_age_seconds == d("86400.000000")
    assert row.status == "block"
    assert "stale_probability_memory" in row.reason_codes
    assert report.status == "block"


def test_same_market_candidates_form_one_row_with_canonical_candidate_digest() -> None:
    canonical_candidate = "candidate://alpha"
    report = build_report(
        (
            observation(1, candidate_id="candidate://zeta"),
            observation(2, candidate_id=canonical_candidate),
        ),
    )

    assert report.row_count == d("1.000000")
    assert report.rows[0].observation_count == d("2.000000")
    assert report.rows[0].candidate_digest == digest(canonical_candidate + "-2")


def test_source_count_accumulates_caller_deduplicated_observation_totals() -> None:
    first = observation(1, source_count=d("2.000000"))
    second = replace(
        observation(2, source_count=d("3.000000")),
        source_reference=first.source_reference,
    )
    report = build_report(
        (first, second),
        cfg=config(min_source_count=d("10.000000")),
    )

    assert report.rows[0].source_count == d("5.000000")
    assert report.rows[0].source_diversity_score == d("0.500000")


def test_candidate_digest_may_repeat_across_distinct_market_rows() -> None:
    candidate = "candidate://shared"
    report = build_report(
        (
            observation(1, candidate_id=candidate, market_id="market-a"),
            observation(1, candidate_id=candidate, market_id="market-b"),
        ),
    )

    assert report.row_count == d("2.000000")
    assert {row.candidate_digest for row in report.rows} == {
        digest(candidate + "-1"),
    }
    assert len({row.market_digest for row in report.rows}) == 2


def test_public_payload_is_deterministic_digest_validated_and_redacted() -> None:
    raw_candidate = "candidate://raw-private?secret=alpha"
    raw_market = "market-question-text: raw market wording should not leak"
    raw_source = (
        "https://vendor.example/private/source?secret=abc "
        "postgres://user:pass@host/private raw paragraph"
    )
    rows = (
        observation(
            2,
            candidate_id=raw_candidate,
            market_id=raw_market,
            source_reference=raw_source,
            probability=d("0.640000"),
            previous_probability=d("0.630000"),
            bid_depth=d("700.000000"),
            ask_depth=d("500.000000"),
            observed_at=GENERATED_AT - timedelta(minutes=30),
        ),
        observation(
            1,
            candidate_id=raw_candidate,
            market_id=raw_market,
            source_reference=raw_source,
        ),
    )

    first = build_report(rows)
    second = build_report(tuple(reversed(rows)))
    first_payload = m().research_market_depth_probability_memory_scorecard_public_payload(
        first,
    )
    second_payload = m().research_market_depth_probability_memory_scorecard_public_payload(
        second,
    )
    body = dict(first_payload)
    validation_digest = body.pop("validation_digest")
    expected_digest = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first.validation_digest == expected_digest
    assert validation_digest == expected_digest
    assert m().validate_research_market_depth_probability_memory_scorecard_report_digest(
        first,
    )
    assert digest(raw_candidate + "-1") in encoded
    assert raw_candidate not in encoded
    assert raw_market not in encoded
    assert raw_source not in encoded
    assert "https://" not in encoded
    assert "postgres://" not in encoded
    assert "raw paragraph" not in encoded
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    with pytest.raises(ValueError, match="validation_digest"):
        replace(first, validation_digest="0" * 64)


def test_signed_zero_has_one_public_payload_and_digest_representation() -> None:
    positive_zero = d("0.000000")
    signed_zero = d("-0.000000")
    positive_observation = observation(
        1,
        probability=positive_zero,
        previous_probability=positive_zero,
        bid_depth=positive_zero,
        ask_depth=positive_zero,
        source_count=positive_zero,
    )
    signed_observation = observation(
        1,
        probability=signed_zero,
        previous_probability=signed_zero,
        bid_depth=signed_zero,
        ask_depth=signed_zero,
        source_count=signed_zero,
    )
    positive_report = build_report((positive_observation,))
    signed_input_report = build_report((signed_observation,))
    signed_row = replace(
        positive_report.rows[0],
        average_depth=signed_zero,
    )
    signed_row_report = replace(
        positive_report,
        rows=(signed_row,),
        validation_digest="",
    )

    positive_payload = (
        m().research_market_depth_probability_memory_scorecard_public_payload(
            positive_report,
        )
    )
    signed_input_payload = (
        m().research_market_depth_probability_memory_scorecard_public_payload(
            signed_input_report,
        )
    )
    signed_row_payload = (
        m().research_market_depth_probability_memory_scorecard_public_payload(
            signed_row_report,
        )
    )

    assert signed_input_payload == positive_payload
    assert signed_row_payload == positive_payload
    assert signed_input_report.validation_digest == positive_report.validation_digest
    assert signed_row_report.validation_digest == positive_report.validation_digest
    assert "-0.000000" not in json.dumps(signed_row_payload, sort_keys=True)
    for field_name in (
        "probability",
        "previous_probability",
        "bid_depth",
        "ask_depth",
        "source_count",
    ):
        assert not getattr(signed_observation, field_name).is_signed()
    assert not signed_row.average_depth.is_signed()


def test_validation_rejects_float_subclass_bad_flags_and_unsupported_status() -> None:
    module = m()
    with pytest.raises(ValueError, match="target_depth"):
        config(target_depth=1000)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="pass_score_min"):
        config(pass_score_min=_DecimalSubclass("0.750000"))
    with pytest.raises(ValueError, match="probability"):
        observation(1, probability=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at"):
        observation(1, observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation(1), paper_only=False)

    report = build_report((observation(1),))
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="status"):
        replace(report, status="blocked")
    with pytest.raises(TypeError):
        type(
            "ChildReport",
            (module.ResearchMarketDepthProbabilityMemoryScorecardReport,),
            {},
        )


def test_decimal_arithmetic_is_independent_of_ambient_context() -> None:
    rows = (
        observation(
            1,
            probability=d("0.987654"),
            previous_probability=d("0.123456"),
            bid_depth=d("123456.123456"),
            ask_depth=d("0.000001"),
        ),
    )
    cfg = config()
    expected = m().research_market_depth_probability_memory_scorecard_public_payload(
        build_report(rows, cfg=cfg),
    )

    with localcontext(Context(prec=4, rounding=ROUND_DOWN)):
        constrained = (
            m().research_market_depth_probability_memory_scorecard_public_payload(
                build_report(rows, cfg=cfg),
            )
        )

    assert constrained == expected


def test_digest_validation_rejects_forged_non_digest_public_identity() -> None:
    report = build_report((observation(1),))
    payload = m().research_market_depth_probability_memory_scorecard_public_payload(
        report,
    )
    body = dict(payload)
    body.pop("validation_digest")
    forged_candidate = "candidate://raw-private?secret=forged"
    body["rows"][0]["candidate_digest"] = forged_candidate
    forged_digest = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()

    object.__setattr__(report.rows[0], "candidate_digest", forged_candidate)
    object.__setattr__(report, "validation_digest", forged_digest)

    assert not m().validate_research_market_depth_probability_memory_scorecard_report_digest(
        report,
    )
    with pytest.raises(ValueError, match="candidate_digest"):
        m().research_market_depth_probability_memory_scorecard_public_payload(report)


def test_public_payload_and_digest_bind_the_exact_scorecard_config() -> None:
    cfg = config(
        target_depth=d("2000.000000"),
        min_source_count=d("4.000000"),
        probability_memory_weight=d("0.500000"),
        market_depth_weight=d("0.300000"),
        source_diversity_weight=d("0.200000"),
    )
    report = build_report((observation(1),), cfg=cfg)
    payload = m().research_market_depth_probability_memory_scorecard_public_payload(
        report,
    )

    assert getattr(report, "config", None) == cfg
    assert payload["config"] == {
        "config_version": (
            "research-market-depth-probability-memory-scorecard-report-v0"
        ),
        "target_depth": "2000.000000",
        "min_source_count": "4.000000",
        "pass_score_min": "0.750000",
        "watch_score_min": "0.450000",
        "stale_memory_age_seconds": "86400.000000",
        "probability_memory_weight": "0.500000",
        "market_depth_weight": "0.300000",
        "source_diversity_weight": "0.200000",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert m().validate_research_market_depth_probability_memory_scorecard_report_digest(
        report,
    )


@pytest.mark.parametrize(
    ("field_name", "forged_value"),
    (
        ("market_depth_score", d("0.750000")),
        ("source_diversity_score", d("0.750000")),
        ("score", d("0.800000")),
    ),
)
def test_resigned_derived_score_forgery_is_rejected(
    field_name: str,
    forged_value: Decimal,
) -> None:
    cfg = config(
        target_depth=d("2000.000000"),
        min_source_count=d("4.000000"),
        probability_memory_weight=d("0.500000"),
        market_depth_weight=d("0.300000"),
        source_diversity_weight=d("0.200000"),
    )
    report = build_report((observation(1),), cfg=cfg)
    payload = m().research_market_depth_probability_memory_scorecard_public_payload(
        report,
    )
    body = dict(payload)
    body.pop("validation_digest")
    body["rows"][0][field_name] = format(forged_value, "f")
    object.__setattr__(report.rows[0], field_name, forged_value)
    if field_name == "score":
        body["average_score"] = format(forged_value, "f")
        object.__setattr__(report, "average_score", forged_value)
    forged_digest = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    object.__setattr__(report, "validation_digest", forged_digest)

    assert not m().validate_research_market_depth_probability_memory_scorecard_report_digest(
        report,
    )
    with pytest.raises(ValueError, match=field_name):
        m().research_market_depth_probability_memory_scorecard_public_payload(report)


def test_owned_module_has_no_runtime_or_decisioning_surface_terms() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_depth_probability_memory_scorecard_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "open(",
        "connect(",
        "wallet",
        "auth",
        "order",
        "live trading",
        "sizing",
        "recommendation",
        "database",
        "dsn",
        "token",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
