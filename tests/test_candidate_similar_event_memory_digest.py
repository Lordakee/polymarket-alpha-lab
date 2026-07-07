from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.candidate_similar_event_memory_digest"
GENERATED_AT = datetime(2026, 7, 7, 15, 30, tzinfo=timezone.utc)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def module() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    digest = module()
    values = {
        "config_version": (
            digest.DEFAULT_CANDIDATE_SIMILAR_EVENT_MEMORY_DIGEST_CONFIG_VERSION
        ),
    }
    values.update(overrides)
    return digest.CandidateSimilarEventMemoryDigestConfig(**values)


def baseline(
    team_id: str = "crypto_btc",
    *,
    historical_candidate_count: Decimal = d("20.000000"),
    historical_pass_ratio: Decimal = d("0.700000"),
    historical_watch_ratio: Decimal = d("0.200000"),
    historical_block_ratio: Decimal = d("0.100000"),
    historical_average_memory_support_score: Decimal = d("0.740000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    digest = module()
    return digest.CandidateSimilarEventTeamMemoryBaseline(
        team_id=team_id,
        historical_candidate_count=historical_candidate_count,
        historical_pass_ratio=historical_pass_ratio,
        historical_watch_ratio=historical_watch_ratio,
        historical_block_ratio=historical_block_ratio,
        historical_average_memory_support_score=historical_average_memory_support_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def fact(
    redacted_candidate_ref: str = "candidate_ref_alpha",
    *,
    team_id: str = "crypto_btc",
    similar_event_count: Decimal = d("8.000000"),
    median_similarity: Decimal = d("0.820000"),
    median_base_rate: Decimal = d("0.550000"),
    outcome_dispersion: Decimal = d("0.200000"),
    average_settlement_quality: Decimal = d("0.900000"),
    recency_score: Decimal = d("0.800000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    digest = module()
    return digest.CandidateSimilarEventMemoryFacts(
        redacted_candidate_ref=redacted_candidate_ref,
        team_id=team_id,
        similar_event_count=similar_event_count,
        median_similarity=median_similarity,
        median_base_rate=median_base_rate,
        outcome_dispersion=outcome_dispersion,
        average_settlement_quality=average_settlement_quality,
        recency_score=recency_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *facts: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
    team_memory_baselines: object = (),
) -> Any:
    digest = module()
    return digest.build_candidate_similar_event_memory_digest(
        facts,
        generated_at=generated_at,
        config=cfg if cfg is not None else config(),
        team_memory_baselines=team_memory_baselines,
    )


def walk_values(value: Any) -> tuple[Any, ...]:
    values = (value,)
    if isinstance(value, dict):
        for item in value.values():
            values += walk_values(item)
    elif isinstance(value, list):
        for item in value:
            values += walk_values(item)
    return values


def rebuild_dataclass(value: Any, **overrides: object) -> Any:
    values = {item.name: getattr(value, item.name) for item in fields(value)}
    values.update(overrides)
    return type(value)(**values)


def test_builds_pass_watch_and_block_rows_deterministically() -> None:
    result = report(
        fact(
            "candidate_ref_pass",
            team_id="crypto_btc",
            similar_event_count=d("9.000000"),
            median_similarity=d("0.830000"),
            median_base_rate=d("0.560000"),
            outcome_dispersion=d("0.220000"),
            average_settlement_quality=d("0.910000"),
            recency_score=d("0.850000"),
        ),
        fact(
            "candidate_ref_block",
            team_id="macro_rates",
            similar_event_count=d("1.000000"),
            median_similarity=d("0.760000"),
            median_base_rate=d("0.480000"),
            outcome_dispersion=d("0.300000"),
            average_settlement_quality=d("0.920000"),
            recency_score=d("0.740000"),
        ),
        fact(
            "candidate_ref_watch",
            team_id="sports_soccer",
            similar_event_count=d("3.000000"),
            median_similarity=d("0.620000"),
            median_base_rate=d("0.970000"),
            outcome_dispersion=d("0.610000"),
            average_settlement_quality=d("0.700000"),
            recency_score=d("0.500000"),
        ),
    )

    assert result.generated_at == GENERATED_AT
    assert result.support_status == "block"
    assert result.report_status == "block"
    assert result.candidate_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.average_memory_support_score == d("0.726833")
    assert tuple(row.support_status for row in result.rows) == (
        "block",
        "watch",
        "pass",
    )
    assert tuple(row.redacted_candidate_ref for row in result.rows) == (
        "candidate_ref_block",
        "candidate_ref_watch",
        "candidate_ref_pass",
    )
    assert result.rows[0].memory_support_score == d("0.782000")
    assert result.rows[1].memory_support_score == d("0.536000")
    assert result.rows[2].memory_support_score == d("0.862500")
    assert result.rows[0].reason_codes == (
        "similar_event_memory_block",
        "similar_event_count_low",
    )
    assert result.rows[1].reason_codes == (
        "similar_event_memory_watch",
        "similar_event_count_watch",
        "median_similarity_watch",
        "settlement_quality_watch",
        "recency_watch",
        "outcome_dispersion_watch",
        "base_rate_extreme",
    )
    assert result.rows[2].reason_codes == ("similar_event_memory_pass",)
    assert result.reason_codes == (
        "similar_event_memory_pass",
        "similar_event_memory_watch",
        "similar_event_memory_block",
        "similar_event_count_low",
        "similar_event_count_watch",
        "median_similarity_watch",
        "settlement_quality_watch",
        "recency_watch",
        "outcome_dispersion_watch",
        "base_rate_extreme",
    )
    count_by_reason = {row.reason_code: row for row in result.reason_code_counts}
    assert count_by_reason["similar_event_memory_pass"].count == d("1")
    assert count_by_reason["similar_event_memory_pass"].candidate_ratio == d("0.333333")
    assert count_by_reason["similar_event_memory_watch"].count == d("1")
    assert count_by_reason["similar_event_memory_block"].count == d("1")


def test_empty_digest_blocks_similar_event_memory_use() -> None:
    result = report()

    assert result.support_status == "block"
    assert result.report_status == "block"
    assert result.candidate_count == ZERO
    assert result.pass_count == ZERO
    assert result.watch_count == ZERO
    assert result.block_count == ZERO
    assert result.average_memory_support_score == ZERO
    assert result.rows == ()
    assert result.reason_codes == ("candidate_similar_event_memory_digest_empty",)
    assert result.reason_code_counts[0].count == d("1")
    assert result.reason_code_counts[0].candidate_ratio == ZERO


def test_payload_is_public_safe_and_uses_decimal_strings() -> None:
    digest = module()
    result = report(
        fact(
            "candidate_ref_public_alpha",
            team_id="crypto_eth",
            similar_event_count=d("6.000000"),
            median_similarity=d("0.780000"),
            median_base_rate=d("0.520000"),
            outcome_dispersion=d("0.250000"),
            average_settlement_quality=d("0.860000"),
            recency_score=d("0.770000"),
        ),
        generated_at=datetime(
            2026,
            7,
            7,
            11,
            30,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )

    payload = digest.candidate_similar_event_memory_digest_payload(result)
    json.dumps(payload, allow_nan=False, sort_keys=True)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()

    assert payload["generated_at"] == "2026-07-07T15:30:00+00:00"
    assert payload["candidate_count"] == "1.000000"
    assert payload["pass_count"] == "1.000000"
    assert payload["average_memory_support_score"] == "0.824000"
    assert payload["historical_candidate_count"] == "0.000000"
    assert payload["memory_support_score_delta"] == "0.000000"
    assert payload["pass_ratio_delta"] == "0.000000"
    assert payload["block_ratio_delta"] == "0.000000"
    assert payload["team_memory_baselines"] == []
    assert payload["rows"][0]["redacted_candidate_ref"] == "candidate_ref_public_alpha"
    assert payload["rows"][0]["similar_event_count"] == "6.000000"
    assert payload["rows"][0]["memory_support_score"] == "0.824000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["paper_only"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert not any(
        type(value) is int and not isinstance(value, bool)
        for value in walk_values(payload)
    )
    assert "re" "ady" not in rendered
    assert "re" "commended" not in rendered
    assert "re" "commend" not in rendered
    for forbidden in (
        "candidate" "_" "id",
        "event" "_" "id",
        "event" "_" "slug",
        "market" "_" "id",
        "market" "_" "slug",
        "ques" "tion",
        "source" "_" "ref",
        "source" "_" "reference",
        "source" "_" "text",
        "condition" "_" "id",
    ):
        assert forbidden not in rendered


def test_supports_team_historical_memory_comparison_without_raw_history() -> None:
    digest = module()
    result = report(
        fact(
            "candidate_ref_btc_pass",
            team_id="crypto_btc",
            similar_event_count=d("8.000000"),
            median_similarity=d("0.820000"),
            median_base_rate=d("0.550000"),
            outcome_dispersion=d("0.200000"),
            average_settlement_quality=d("0.900000"),
            recency_score=d("0.800000"),
        ),
        fact(
            "candidate_ref_rates_watch",
            team_id="macro_rates",
            similar_event_count=d("3.000000"),
            median_similarity=d("0.610000"),
            median_base_rate=d("0.500000"),
            outcome_dispersion=d("0.600000"),
            average_settlement_quality=d("0.700000"),
            recency_score=d("0.500000"),
        ),
        team_memory_baselines=(
            baseline(
                "crypto_btc",
                historical_candidate_count=d("12.000000"),
                historical_pass_ratio=d("0.500000"),
                historical_watch_ratio=d("0.250000"),
                historical_block_ratio=d("0.250000"),
                historical_average_memory_support_score=d("0.750000"),
            ),
            baseline(
                "macro_rates",
                historical_candidate_count=d("9.000000"),
                historical_pass_ratio=d("0.200000"),
                historical_watch_ratio=d("0.500000"),
                historical_block_ratio=d("0.300000"),
                historical_average_memory_support_score=d("0.600000"),
            ),
        ),
    )

    assert result.team_count == d("2.000000")
    assert result.historical_candidate_count == d("21.000000")
    assert result.historical_average_memory_support_score == d("0.685714")
    assert result.memory_support_score_delta == d("0.053786")
    assert result.pass_ratio_delta == d("0.128571")
    assert result.block_ratio_delta == d("-0.271429")
    assert result.team_memory_baselines == (
        baseline(
            "crypto_btc",
            historical_candidate_count=d("12.000000"),
            historical_pass_ratio=d("0.500000"),
            historical_watch_ratio=d("0.250000"),
            historical_block_ratio=d("0.250000"),
            historical_average_memory_support_score=d("0.750000"),
        ),
        baseline(
            "macro_rates",
            historical_candidate_count=d("9.000000"),
            historical_pass_ratio=d("0.200000"),
            historical_watch_ratio=d("0.500000"),
            historical_block_ratio=d("0.300000"),
            historical_average_memory_support_score=d("0.600000"),
        ),
    )

    payload = digest.candidate_similar_event_memory_digest_payload(result)
    json.dumps(payload, allow_nan=False, sort_keys=True)
    assert payload["team_count"] == "2.000000"
    assert payload["historical_candidate_count"] == "21.000000"
    assert payload["historical_average_memory_support_score"] == "0.685714"
    assert payload["memory_support_score_delta"] == "0.053786"
    assert payload["pass_ratio_delta"] == "0.128571"
    assert payload["block_ratio_delta"] == "-0.271429"
    assert payload["team_memory_baselines"] == [
        {
            "team_id": "crypto_btc",
            "historical_candidate_count": "12.000000",
            "historical_pass_ratio": "0.500000",
            "historical_watch_ratio": "0.250000",
            "historical_block_ratio": "0.250000",
            "historical_average_memory_support_score": "0.750000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "team_id": "macro_rates",
            "historical_candidate_count": "9.000000",
            "historical_pass_ratio": "0.200000",
            "historical_watch_ratio": "0.500000",
            "historical_block_ratio": "0.300000",
            "historical_average_memory_support_score": "0.600000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert not any(
        type(value) is int and not isinstance(value, bool)
        for value in walk_values(payload)
    )


def test_rejects_unsafe_public_surface_strings() -> None:
    digest = module()

    for unsafe_ref in (
        "candidate_ref_" "h" "ttp_" "u" "rl",
        "candidate_ref_" "source" "_" "u" "rl",
        "candidate_ref_" "source" "_" "text",
        "candidate_ref_" "raw" "_" "text",
        "candidate_ref_" "candidate" "_" "id",
        "candidate_ref_" "market" "_" "id",
        "candidate_ref_" "d" "sn",
        "candidate_ref_" "table" "_" "name",
        "candidate_ref_" "private" "_" "key",
        "candidate_ref_" "au" "th_" "to" "ken",
        "candidate_ref_" "wal" "let",
        "candidate_ref_" "tra" "de",
        "candidate_ref_" "b" "uy",
        "candidate_ref_" "se" "ll",
        "candidate_ref_" "or" "der",
        "candidate_ref_" "si" "gn_" "or" "der",
        "candidate_ref_" "can" "cel_" "or" "der",
        "candidate_ref_" "re" "place_" "or" "der",
        "candidate_ref_" "pos" "ition",
        "candidate_ref_" "si" "ze",
        "candidate_ref_" "pri" "ce",
        "candidate_ref_" "re" "commendation",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            fact(redacted_candidate_ref=unsafe_ref)

    with pytest.raises(ValueError, match="team_memory_baselines"):
        report(fact(), team_memory_baselines=(baseline(), baseline()))
    with pytest.raises(ValueError, match="team_memory_baselines"):
        report(fact(team_id="crypto_eth"), team_memory_baselines=(baseline("crypto_btc"),))

    unsafe_report = report(fact())
    object.__setattr__(unsafe_report, "report_status", "place_" "or" "der")
    with pytest.raises(ValueError, match="unsafe"):
        digest.candidate_similar_event_memory_digest_payload(unsafe_report)
    unsafe_team_report = report(fact())
    object.__setattr__(
        unsafe_team_report.rows[0],
        "team_id",
        "crypto_btc_" "source" "_" "u" "rl",
    )
    with pytest.raises(ValueError, match="unsafe"):
        digest.candidate_similar_event_memory_digest_payload(unsafe_team_report)


def test_public_payload_uses_pass_watch_block_vocabulary_only() -> None:
    digest = module()
    result = report(
        fact(
            "candidate_ref_pass_vocab",
            similar_event_count=d("7.000000"),
            median_similarity=d("0.760000"),
            median_base_rate=d("0.500000"),
            outcome_dispersion=d("0.250000"),
            average_settlement_quality=d("0.850000"),
            recency_score=d("0.760000"),
        ),
    )

    assert result.support_status == "pass"
    assert result.report_status == "pass"
    assert result.pass_count == d("1.000000")
    assert not hasattr(result, "re" "ady_count")
    assert not hasattr(result, "re" "commended_next_step")

    payload = digest.candidate_similar_event_memory_digest_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()

    assert payload["support_status"] == "pass"
    assert payload["report_status"] == "pass"
    assert payload["pass_count"] == "1.000000"
    assert "re" "ady" not in rendered
    assert "re" "commended" not in rendered
    assert "re" "commendation" not in rendered


def test_rejects_raw_surface_fragments_bad_types_and_flag_downgrades() -> None:
    digest = module()

    with pytest.raises(ValueError, match="redacted_candidate_ref"):
        fact(redacted_candidate_ref="market" "_" "slug_alpha")
    with pytest.raises(ValueError, match="team_id"):
        fact(team_id="unknown_team")
    with pytest.raises(ValueError, match="similar_event_count"):
        fact(similar_event_count=d("1.25"))
    with pytest.raises(ValueError, match="median_similarity"):
        fact(median_similarity=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="median_base_rate"):
        fact(median_base_rate=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="paper_only"):
        fact(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        digest.build_candidate_similar_event_memory_digest(
            (),
            generated_at=GENERATED_AT,
            config=object(),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        report(fact(), generated_at=datetime(2026, 7, 7, 15, 30))


def test_frozen_dataclasses_exact_exports_and_consistency_validation() -> None:
    digest = module()
    result = report(fact())

    assert digest.__all__ == (
        "DEFAULT_CANDIDATE_SIMILAR_EVENT_MEMORY_DIGEST_CONFIG_VERSION",
        "CandidateSimilarEventMemoryDigestConfig",
        "CandidateSimilarEventTeamMemoryBaseline",
        "CandidateSimilarEventMemoryFacts",
        "CandidateSimilarEventMemoryDigestRow",
        "CandidateSimilarEventMemoryReasonCodeCount",
        "CandidateSimilarEventMemoryDigestReport",
        "build_candidate_similar_event_memory_digest",
        "candidate_similar_event_memory_digest_payload",
    )
    for exported_name in digest.__all__:
        exported = getattr(digest, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    frozen = fact(redacted_candidate_ref="candidate_ref_frozen")
    with pytest.raises(FrozenInstanceError):
        frozen.team_id = "macro_rates"  # type: ignore[misc]
    with pytest.raises(TypeError, match="does not support subclassing"):
        type(
            "ConfigSubclass",
            (digest.CandidateSimilarEventMemoryDigestConfig,),
            {},
        )
    with pytest.raises(ValueError, match="rows"):
        rebuild_dataclass(result, rows=())
    with pytest.raises(ValueError, match="reason_codes"):
        rebuild_dataclass(result.rows[0], reason_codes=("similar_event_memory_watch",))
    with pytest.raises(ValueError, match="team_count"):
        rebuild_dataclass(result, team_count=d("9.000000"))
    with pytest.raises(ValueError, match="memory_support_score_delta"):
        rebuild_dataclass(result, memory_support_score_delta=d("2.000000"))

    for value in (
        result,
        *result.team_memory_baselines,
        *result.rows,
        *result.reason_code_counts,
    ):
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item.name.endswith(
                (
                    "_count",
                    "_ratio",
                    "_score",
                    "_rate",
                    "_similarity",
                    "_dispersion",
                    "_quality",
                ),
            ):
                assert type(item_value) is Decimal


def test_output_is_deterministic_for_input_sequence_changes() -> None:
    digest = module()
    facts = (
        fact("candidate_ref_zulu", team_id="macro_rates"),
        fact("candidate_ref_alpha", team_id="macro_rates"),
        fact(
            "candidate_ref_bravo",
            team_id="macro_rates",
            similar_event_count=d("2.000000"),
            median_similarity=d("0.590000"),
            median_base_rate=d("0.500000"),
            outcome_dispersion=d("0.700000"),
            average_settlement_quality=d("0.650000"),
            recency_score=d("0.450000"),
        ),
    )

    first = digest.candidate_similar_event_memory_digest_payload(report(*facts))
    second = digest.candidate_similar_event_memory_digest_payload(report(*reversed(facts)))

    assert first == second
    assert tuple(row["redacted_candidate_ref"] for row in first["rows"]) == (
        "candidate_ref_bravo",
        "candidate_ref_alpha",
        "candidate_ref_zulu",
    )


def test_output_is_deterministic_for_team_memory_baseline_sequence_changes() -> None:
    digest = module()
    facts = (
        fact("candidate_ref_btc", team_id="crypto_btc"),
        fact("candidate_ref_rates", team_id="macro_rates"),
    )
    baselines = (
        baseline("crypto_btc"),
        baseline(
            "macro_rates",
            historical_candidate_count=d("10.000000"),
            historical_pass_ratio=d("0.600000"),
            historical_watch_ratio=d("0.300000"),
            historical_block_ratio=d("0.100000"),
            historical_average_memory_support_score=d("0.700000"),
        ),
    )

    first = digest.candidate_similar_event_memory_digest_payload(
        report(*facts, team_memory_baselines=baselines),
    )
    second = digest.candidate_similar_event_memory_digest_payload(
        report(*facts, team_memory_baselines=tuple(reversed(baselines))),
    )

    assert first == second
    assert tuple(row["team_id"] for row in first["team_memory_baselines"]) == (
        "crypto_btc",
        "macro_rates",
    )


def test_static_pure_phase_one_boundary() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src/polymarket_alpha_lab/candidate_similar_event_memory_digest.py"
    )
    source = source_path.read_text()
    lowered_source = source.lower()

    forbidden_terms = (
        "acc" "ount",
        "api" "_" "key",
        "au" "th",
        "can" "cel",
        "dotenv",
        "ex" "change",
        "private" "_" "key",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "supabase",
        "u" "rllib",
        "wal" "let",
        "web3",
    )
    for term in forbidden_terms:
        assert term not in lowered_source
    assert "os.environ" not in lowered_source

    public_surface_fragments = (
        "candidate" "_" "id",
        "event" "_" "id",
        "event" "_" "slug",
        "market" "_" "id",
        "market" "_" "slug",
        "condition" "_" "id",
        "source" "_" "ref",
        "source" "_" "u" "rl",
        "raw" "_" "text",
        "source" "_" "text",
        "database" "_" "u" "rl",
        "table" "_" "name",
        "private" "_" "key",
        "b" "uy",
        "se" "ll",
        "tra" "de",
        "or" "der",
        "pos" "ition",
        "si" "ze",
        "pri" "ce",
        "sta" "ke",
        "sha" "res",
        "re" "commend",
    )
    for fragment in public_surface_fragments:
        assert fragment not in lowered_source

    tree = ast.parse(source)
    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "h" "ttp",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "supabase",
        "u" "rllib",
        "web3",
    )
    forbidden_call_names = {
        "connect",
        "execute",
        "executemany",
        "getenv",
        "open",
        "patch",
        "post",
        "put",
        "read",
        "request",
        "run",
        "system",
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
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError(f"float literal found: {node.value!r}")

    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
