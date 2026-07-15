from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, ROUND_DOWN, localcontext
from hashlib import sha256
import json
from pathlib import Path

import pytest

import polymarket_alpha_lab.research_strategy_cross_team_claim_authority_decay_report as module
from polymarket_alpha_lab.research_strategy_cross_team_claim_authority_decay_report import (
    CrossTeamClaimAuthorityDecayConfig,
    CrossTeamClaimAuthorityDecayObservation,
    CrossTeamClaimAuthorityDecayReasonCodeCount,
    CrossTeamClaimAuthorityDecayReport,
    CrossTeamClaimAuthorityDecayRow,
    build_research_strategy_cross_team_claim_authority_decay_report,
    research_strategy_cross_team_claim_authority_decay_report_payload,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> CrossTeamClaimAuthorityDecayConfig:
    values = {
        "config_version": "cross-team-claim-authority-decay-report-v0",
        "fresh_age_seconds": d("3600"),
        "stale_age_seconds": d("86400"),
        "cross_team_weight": d("0.450000"),
        "authority_weight": d("0.350000"),
        "recency_weight": d("0.200000"),
        "pass_authority_score": d("0.700000"),
        "watch_authority_score": d("0.400000"),
    }
    values.update(overrides)
    return CrossTeamClaimAuthorityDecayConfig(**values)


def observation(
    index: int,
    *,
    claim_id: str = "claim-alpha",
    observation_id: str | None = None,
    team_id: str = "team-a",
    authority_id: str = "authority-a",
    source_label: str = "source-a",
    cross_team_confirmations: Decimal | None = None,
    total_confirmations: Decimal | None = None,
    authority_confidence: Decimal = d("0.900000"),
    observed_at: datetime | None = None,
    reason_codes: tuple[str, ...] = (),
) -> CrossTeamClaimAuthorityDecayObservation:
    return CrossTeamClaimAuthorityDecayObservation(
        claim_id=claim_id,
        observation_id=(
            f"observation-{index:03d}" if observation_id is None else observation_id
        ),
        team_id=team_id,
        authority_id=authority_id,
        source_label=source_label,
        cross_team_confirmations=(
            d("2") if cross_team_confirmations is None else cross_team_confirmations
        ),
        total_confirmations=d("3") if total_confirmations is None else total_confirmations,
        authority_confidence=authority_confidence,
        observed_at=(
            GENERATED_AT - timedelta(minutes=30)
            if observed_at is None
            else observed_at
        ),
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: CrossTeamClaimAuthorityDecayConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> CrossTeamClaimAuthorityDecayReport:
    return build_research_strategy_cross_team_claim_authority_decay_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_blocked_report_only_digest() -> None:
    authority_report = report(())

    assert type(authority_report) is CrossTeamClaimAuthorityDecayReport
    assert authority_report.generated_at == GENERATED_AT
    assert authority_report.config_version == "cross-team-claim-authority-decay-report-v0"
    assert authority_report.claim_count == d("0")
    assert authority_report.observation_count == d("0")
    assert authority_report.pass_count == d("0")
    assert authority_report.watch_count == d("0")
    assert authority_report.block_count == d("0")
    assert authority_report.average_authority_score is None
    assert authority_report.status == "block"
    assert authority_report.rows == ()
    assert authority_report.reason_code_counts == (
        CrossTeamClaimAuthorityDecayReasonCodeCount("no_claim_authority_observations", d("1")),
    )
    assert authority_report.reason_codes == ("no_claim_authority_observations",)
    assert authority_report.paper_only is True
    assert authority_report.report_only is True
    assert authority_report.readonly is True


def test_cross_team_authority_decay_scores_claims_deterministically() -> None:
    authority_report = report(
        (
            observation(
                2,
                claim_id="claim-z",
                team_id="team-b",
                authority_id="authority-b",
                source_label="hashed-source-b",
                cross_team_confirmations=d("1"),
                total_confirmations=d("4"),
                authority_confidence=d("0.500000"),
                observed_at=GENERATED_AT - timedelta(days=2),
                reason_codes=("manual_reviewed",),
            ),
            observation(
                1,
                claim_id="claim-a",
                team_id="team-a",
                authority_id="authority-a",
                source_label="hashed-source-a",
            ),
        ),
    )

    assert tuple(row.claim_id for row in authority_report.rows) == ("claim-a", "claim-z")
    assert authority_report.status == "block"
    assert authority_report.claim_count == d("2")
    assert authority_report.observation_count == d("2")
    assert authority_report.pass_count == d("1")
    assert authority_report.watch_count == d("0")
    assert authority_report.block_count == d("1")
    assert authority_report.average_authority_score == d("0.551250")
    assert authority_report.reason_codes == (
        "claim_authority_decay_block",
        "claim_authority_decay_pass",
    )

    pass_row, block_row = authority_report.rows
    assert pass_row == CrossTeamClaimAuthorityDecayRow(
        claim_id="claim-a",
        observation_count=d("1"),
        team_count=d("1"),
        authority_count=d("1"),
        source_count=d("1"),
        latest_observed_at=GENERATED_AT - timedelta(minutes=30),
        latest_source_age_seconds=d("1800"),
        cross_team_confirmation_score=d("0.666667"),
        authority_confidence_score=d("0.900000"),
        recency_score=d("1.000000"),
        authority_score=d("0.815000"),
        observation_ids=("observation-001",),
        team_ids=("team-a",),
        authority_ids=("authority-a",),
        source_labels=("hashed-source-a",),
        status="pass",
        reason_codes=(
            "authority_confidence_strong",
            "claim_authority_decay_pass",
            "fresh_authority_observations",
        ),
    )
    assert block_row.status == "block"
    assert block_row.authority_score == d("0.287500")
    assert block_row.reason_codes == (
        "claim_authority_decay_block",
        "input_manual_reviewed",
        "stale_authority_observations",
        "weak_authority_confidence",
        "weak_cross_team_confirmation",
    )


def test_payload_is_public_deterministic_decimal_only_and_digest_validated() -> None:
    authority_report = report(
        (
            observation(2, claim_id="private-row-b", source_label="opaque-source-b"),
            observation(1, claim_id="private-row-a", source_label="opaque-source-a"),
        ),
    )

    payload = research_strategy_cross_team_claim_authority_decay_report_payload(
        authority_report,
    )
    digest_payload = dict(payload)
    digest_payload.pop("digest")
    encoded = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    expected_digest = sha256(encoded.encode("utf-8")).hexdigest()

    assert payload["digest"] == expected_digest
    assert payload["digest"] == authority_report.digest
    assert research_strategy_cross_team_claim_authority_decay_report_payload(
        authority_report,
    ) == payload
    assert payload["rows"][0]["claim_key"] == "claim:9579d00af9157468"
    assert payload["rows"][0]["observation_keys"] == ["observation:24c3958ad0cc203e"]
    assert payload["rows"][0]["authority_score"] == "0.815000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert _payload_text(payload).find("private-row-a") == -1
    assert _payload_text(payload).find("observation-001") == -1
    assert _payload_text(payload).find("opaque-source-a") == -1


def test_payload_rejects_digest_mismatch_and_public_leakage() -> None:
    authority_report = report((observation(1),))

    with pytest.raises(ValueError, match="digest"):
        research_strategy_cross_team_claim_authority_decay_report_payload(
            replace(authority_report, digest="0" * 64),
        )

    with pytest.raises(ValueError, match="unsafe public payload"):
        research_strategy_cross_team_claim_authority_decay_report_payload(
            replace(
                authority_report,
                reason_codes=(
                    "candidate_market_leak",
                    "claim_authority_decay_pass",
                ),
                digest="",
            ),
        )


def test_payload_rejects_sensitive_identifier_terms_in_public_reason_codes() -> None:
    for reason_code in (
        "token_secret",
        "wallet_identifier",
        "order_trade_identifier",
        "private_table_reference",
        "dsn_locator",
    ):
        authority_report = report((observation(1, reason_codes=(reason_code,)),))

        with pytest.raises(ValueError, match="unsafe public payload"):
            research_strategy_cross_team_claim_authority_decay_report_payload(
                authority_report,
            )


def test_decimal_math_and_digest_ignore_ambient_context() -> None:
    values = dict(
        cross_team_confirmations=d("7"),
        total_confirmations=d("13"),
        authority_confidence=d("0.8123456"),
        observed_at=GENERATED_AT - timedelta(hours=5),
    )
    baseline = report((observation(1, **values),))

    with localcontext(Context(prec=3, rounding=ROUND_DOWN)):
        constrained = report((observation(1, **values),))

    assert constrained == baseline
    assert research_strategy_cross_team_claim_authority_decay_report_payload(
        constrained,
    ) == research_strategy_cross_team_claim_authority_decay_report_payload(baseline)


@pytest.mark.parametrize(
    ("field_name", "factory"),
    (
        ("cross_team_confirmations", lambda: observation(1, cross_team_confirmations=d("-0"))),
        ("total_confirmations", lambda: observation(1, total_confirmations=d("-0"))),
        ("authority_confidence", lambda: observation(1, authority_confidence=d("-0"))),
    ),
)
def test_signed_zero_inputs_are_rejected(
    field_name: str,
    factory: object,
) -> None:
    with pytest.raises(ValueError, match=f"{field_name}.*signed zero"):
        factory()  # type: ignore[operator]


def test_dataclasses_are_frozen_slotted_final_and_exact() -> None:
    sample_config = config()
    sample_observation = observation(1)
    sample_report = report((sample_observation,))
    sample_row = sample_report.rows[0]
    sample_reason_count = sample_report.reason_code_counts[0]

    for item in (
        sample_config,
        sample_observation,
        sample_row,
        sample_reason_count,
        sample_report,
    ):
        assert is_dataclass(item)
        assert all(field.name for field in fields(item))
        assert hasattr(type(item), "__slots__")
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]

    for cls in (
        CrossTeamClaimAuthorityDecayConfig,
        CrossTeamClaimAuthorityDecayObservation,
        CrossTeamClaimAuthorityDecayRow,
        CrossTeamClaimAuthorityDecayReasonCodeCount,
        CrossTeamClaimAuthorityDecayReport,
    ):
        assert getattr(cls, "__final__", False) is True
        assert type(cls.__new__(cls)) is cls


def test_direct_row_rejects_forged_authority_score() -> None:
    row = report((observation(1),)).rows[0]

    with pytest.raises(ValueError, match="authority_score"):
        replace(row, authority_score=d("0.100000"))


def test_direct_row_rejects_forged_recency_score() -> None:
    row = report((observation(1),)).rows[0]

    with pytest.raises(ValueError, match="recency_score"):
        replace(row, recency_score=d("0.100000"))


def test_input_rejects_duplicate_observation_identity() -> None:
    item = observation(1)

    with pytest.raises(ValueError, match="observation_id must be unique"):
        report((item, item))


def test_payload_uses_canonical_utc_and_rejects_forged_resigned_counts() -> None:
    built = report((observation(1),))
    payload = research_strategy_cross_team_claim_authority_decay_report_payload(built)

    assert payload["generated_at"] == "2026-07-09T12:00:00Z"
    assert module.validate_research_strategy_cross_team_claim_authority_decay_report_payload(
        payload,
    ) == payload

    forged = json.loads(json.dumps(payload))
    forged["claim_count"] = "2.000000"
    forged["digest"] = _resign_payload(forged)["digest"]
    with pytest.raises(ValueError, match="claim_count"):
        module.validate_research_strategy_cross_team_claim_authority_decay_report_payload(
            forged,
        )


def test_payload_validator_rejects_noncanonical_decimal_and_schema_order() -> None:
    payload = research_strategy_cross_team_claim_authority_decay_report_payload(
        report((observation(1),)),
    )

    noncanonical = json.loads(json.dumps(payload))
    noncanonical["claim_count"] = "1"
    noncanonical["digest"] = _resign_payload(noncanonical)["digest"]
    with pytest.raises(ValueError, match="claim_count"):
        module.validate_research_strategy_cross_team_claim_authority_decay_report_payload(
            noncanonical,
        )

    reordered = dict(reversed(tuple(payload.items())))
    with pytest.raises(ValueError, match="canonical sequence"):
        module.validate_research_strategy_cross_team_claim_authority_decay_report_payload(
            reordered,
        )


def test_resigned_payload_rejects_forged_derived_score() -> None:
    payload = research_strategy_cross_team_claim_authority_decay_report_payload(
        report((observation(1),)),
    )
    forged = json.loads(json.dumps(payload))
    forged["rows"][0]["authority_score"] = "0.100000"
    forged["average_authority_score"] = "0.100000"
    forged["digest"] = _resign_payload(forged)["digest"]

    with pytest.raises(ValueError, match="authority_score"):
        module.validate_research_strategy_cross_team_claim_authority_decay_report_payload(
            forged,
        )


def test_validation_is_strict_decimal_only_frozen_and_report_only() -> None:
    authority_report = report((observation(1),))

    with pytest.raises(FrozenInstanceError):
        authority_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        authority_report.rows[0].authority_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="cross_team_weight"):
        config(cross_team_weight=d("0.100000"))
    with pytest.raises(ValueError, match="pass_authority_score"):
        config(pass_authority_score=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_authority_score"):
        config(watch_authority_score=DecimalSubclass("0.400000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation(1),), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (observation(1),),
            generated_at=DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="status"):
        replace(authority_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation(1), paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(authority_report, readonly=False)


def test_public_payload_never_exposes_raw_candidate_market_source_or_secret_text() -> None:
    authority_report = report(
        (
            observation(
                1,
                claim_id="candidate-market-123",
                observation_id="source-url-row-1",
                authority_id="authority-token-secret",
                source_label="postgres://token@example.com/private_table",
                reason_codes=("safe_reason",),
            ),
        ),
    )

    payload_text = _payload_text(
        research_strategy_cross_team_claim_authority_decay_report_payload(
            authority_report,
        ),
    )

    forbidden_fragments = (
        "candidate-market-123",
        "source-url-row-1",
        "authority-token-secret",
        "postgres://token@example.com/private_table",
        "private_table",
        "token",
        "postgres",
        "source_label",
        "source_labels",
        "authority_id",
        "observation_id",
        "claim_id",
    )
    assert all(fragment not in payload_text for fragment in forbidden_fragments)


def test_owned_module_has_no_db_network_wallet_order_or_live_trading_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_strategy_cross_team_claim_authority_decay_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "dsn",
        "database",
        "db",
        "wallet",
        "authentication",
        "authorization",
        "api_key",
        "token",
        "order",
        "trade",
        "trading",
        "position_size",
        "sizing",
        "recommend",
        "open(",
        "connect(",
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


def _payload_text(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _resign_payload(payload: dict[str, object]) -> dict[str, object]:
    resigned = json.loads(json.dumps(payload))
    digest_values = dict(resigned)
    digest_values.pop("digest", None)
    canonical = json.dumps(
        digest_values,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    resigned["digest"] = sha256(canonical.encode("utf-8")).hexdigest()
    return resigned
