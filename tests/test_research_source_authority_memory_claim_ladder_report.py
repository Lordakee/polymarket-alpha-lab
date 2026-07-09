from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
import importlib
import json
from pathlib import Path
import re
from types import ModuleType

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedClaimShape:
    claim_id: str
    private_candidate_reference: str
    private_market_reference: str
    private_source_reference: str
    authority_tier: str
    observed_at: datetime
    memory_confidence: Decimal
    corroboration_count: Decimal
    contradiction_count: Decimal = Decimal("0")
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def module() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.research_source_authority_memory_claim_ladder_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(mod: ModuleType, **overrides: object) -> object:
    values = {
        "config_version": "research-source-authority-memory-claim-ladder-report-v0",
        "fresh_memory_seconds": d("3600"),
        "stale_memory_seconds": d("86400"),
        "min_corroboration_count": d("2"),
        "pass_ladder_score": d("0.750000"),
        "watch_ladder_score": d("0.400000"),
        "authority_weight": d("0.500000"),
        "memory_weight": d("0.300000"),
        "corroboration_weight": d("0.200000"),
        "contradiction_penalty": d("0.250000"),
    }
    values.update(overrides)
    return mod.ResearchSourceAuthorityMemoryClaimLadderConfig(**values)


def claim(
    mod: ModuleType,
    index: int,
    *,
    claim_id: str = "claim-alpha",
    private_candidate_reference: str | None = None,
    private_market_reference: str | None = None,
    private_source_reference: str | None = None,
    authority_tier: str = "official",
    observed_at: datetime | None = None,
    memory_confidence: Decimal = d("1.000000"),
    corroboration_count: Decimal = d("2"),
    contradiction_count: Decimal = d("0"),
    reason_codes: tuple[str, ...] = (),
) -> object:
    return mod.ResearchSourceAuthorityMemoryClaimLadderClaim(
        claim_id=claim_id,
        private_candidate_reference=(
            private_candidate_reference or f"candidate-private-{index:03d}"
        ),
        private_market_reference=private_market_reference or f"market-private-{index:03d}",
        private_source_reference=private_source_reference or f"source-private-{index:03d}",
        authority_tier=authority_tier,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        memory_confidence=memory_confidence,
        corroboration_count=corroboration_count,
        contradiction_count=contradiction_count,
        reason_codes=reason_codes,
    )


def report(
    mod: ModuleType,
    rows: tuple[object, ...],
    *,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> object:
    return mod.build_research_source_authority_memory_claim_ladder_report(
        rows,
        config=cfg or config(mod),
        generated_at=generated_at,
    )


def test_builds_pass_watch_and_block_ladder_with_decimal_only_scores() -> None:
    mod = module()

    ladder_report = report(
        mod,
        (
            claim(
                mod,
                3,
                claim_id="claim-block",
                authority_tier="secondary",
                observed_at=GENERATED_AT - timedelta(days=2),
                memory_confidence=d("0.900000"),
                corroboration_count=d("0"),
                contradiction_count=d("1"),
                reason_codes=("source_conflict",),
            ),
            claim(
                mod,
                1,
                claim_id="claim-pass",
                authority_tier="official",
                observed_at=GENERATED_AT - timedelta(minutes=30),
                memory_confidence=d("1.000000"),
                corroboration_count=d("2"),
            ),
            claim(
                mod,
                2,
                claim_id="claim-watch",
                authority_tier="secondary",
                observed_at=GENERATED_AT - timedelta(hours=12),
                memory_confidence=d("0.800000"),
                corroboration_count=d("1"),
            ),
        ),
    )

    assert type(ladder_report) is mod.ResearchSourceAuthorityMemoryClaimLadderReport
    assert ladder_report.status == "block"
    assert ladder_report.claim_count == d("3")
    assert ladder_report.pass_count == d("1")
    assert ladder_report.watch_count == d("1")
    assert ladder_report.block_count == d("1")
    assert ladder_report.paper_only is True
    assert ladder_report.report_only is True
    assert ladder_report.readonly is True

    assert tuple(row.claim_id for row in ladder_report.rows) == (
        "claim-block",
        "claim-pass",
        "claim-watch",
    )
    assert tuple(row.status for row in ladder_report.rows) == ("block", "pass", "watch")
    assert {row.status for row in ladder_report.rows} <= {"pass", "watch", "block"}

    pass_row = ladder_report.rows[1]
    assert pass_row.authority_score == d("0.900000")
    assert pass_row.memory_score == d("1.000000")
    assert pass_row.corroboration_score == d("1.000000")
    assert pass_row.contradiction_penalty_score == d("0.000000")
    assert pass_row.claim_ladder_score == d("0.950000")
    assert pass_row.reason_codes == (
        "authority_tier_official",
        "corroborated_claim",
        "fresh_memory",
        "source_authority_memory_claim_ladder_pass",
    )

    block_row = ladder_report.rows[0]
    assert block_row.source_age_seconds == d("172800")
    assert block_row.memory_score == d("0.000000")
    assert block_row.claim_ladder_score == d("0.000000")
    assert block_row.reason_codes == (
        "authority_tier_secondary",
        "contradiction_present",
        "input_source_conflict",
        "low_claim_ladder_score",
        "source_authority_memory_claim_ladder_block",
        "stale_memory",
        "thin_corroboration",
    )

    assert all(
        type(value) not in (int, float, Decimal)
        for value in _walk_payload_values(
            mod.research_source_authority_memory_claim_ladder_report_payload(
                ladder_report,
            ),
        )
    )


def test_public_payload_is_deterministic_redacted_and_digest_validated() -> None:
    mod = module()
    raw_candidate = "candidate raw value with settlement narrative"
    raw_market = "https://example.invalid/markets/private-slug?private=value"
    raw_source = "postgresql://reader:secret@example.invalid/private_table"

    first_report = report(
        mod,
        (
            claim(
                mod,
                2,
                claim_id="claim-zeta",
                private_candidate_reference=raw_candidate,
                private_market_reference=raw_market,
                private_source_reference=raw_source,
                authority_tier="official",
            ),
            claim(
                mod,
                1,
                claim_id="claim-alpha",
                private_candidate_reference="candidate-alpha-private",
                private_market_reference="market-alpha-private",
                private_source_reference="source-alpha-private",
                authority_tier="primary_record",
            ),
        ),
    )
    second_report = report(
        mod,
        (
            claim(
                mod,
                1,
                claim_id="claim-alpha",
                private_candidate_reference="candidate-alpha-private",
                private_market_reference="market-alpha-private",
                private_source_reference="source-alpha-private",
                authority_tier="primary_record",
            ),
            claim(
                mod,
                2,
                claim_id="claim-zeta",
                private_candidate_reference=raw_candidate,
                private_market_reference=raw_market,
                private_source_reference=raw_source,
                authority_tier="official",
            ),
        ),
    )

    payload = mod.research_source_authority_memory_claim_ladder_report_payload(
        first_report,
    )
    payload_again = mod.research_source_authority_memory_claim_ladder_report_payload(
        second_report,
    )

    assert payload == payload_again
    assert tuple(payload) == (
        "generated_at",
        "config_version",
        "claim_count",
        "pass_count",
        "watch_count",
        "block_count",
        "mean_claim_ladder_score",
        "status",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "paper_only",
        "report_only",
        "readonly",
        "public_payload_sha256",
    )
    assert tuple(payload["reason_code_counts"][0]) == (
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(payload["rows"][0]) == (
        "claim_id",
        "candidate_ref_digest",
        "market_ref_digest",
        "source_ref_digest",
        "authority_tier",
        "observed_at",
        "source_age_seconds",
        "authority_score",
        "memory_score",
        "corroboration_score",
        "contradiction_penalty_score",
        "claim_ladder_score",
        "pass_ladder_score",
        "watch_ladder_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert payload["rows"][0]["claim_id"] == "claim-alpha"
    assert payload["rows"][1]["candidate_ref_digest"] == (
        "sha256:" + sha256(raw_candidate.encode("utf-8")).hexdigest()
    )
    assert payload["rows"][1]["market_ref_digest"] == (
        "sha256:" + sha256(raw_market.encode("utf-8")).hexdigest()
    )
    assert payload["rows"][1]["source_ref_digest"] == (
        "sha256:" + sha256(raw_source.encode("utf-8")).hexdigest()
    )

    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    for raw_value in (raw_candidate, raw_market, raw_source):
        assert raw_value not in encoded
    for unsafe_public_key in ("private", "url", "dsn", "table", "token", "text"):
        assert unsafe_public_key not in encoded.lower()

    digest_material = dict(payload)
    digest = digest_material.pop("public_payload_sha256")
    assert digest == sha256(
        json.dumps(
            digest_material,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    assert (
        mod.research_source_authority_memory_claim_ladder_report_public_digest(
            first_report,
        )
        == digest
    )

    with pytest.raises(ValueError, match="public_payload_sha256"):
        replace(first_report, public_payload_sha256="0" * 64)


def test_empty_input_returns_block_report_with_valid_digest() -> None:
    mod = module()

    ladder_report = report(mod, ())
    payload = mod.research_source_authority_memory_claim_ladder_report_payload(
        ladder_report,
    )

    assert ladder_report.status == "block"
    assert ladder_report.claim_count == d("0")
    assert ladder_report.pass_count == d("0")
    assert ladder_report.watch_count == d("0")
    assert ladder_report.block_count == d("0")
    assert ladder_report.mean_claim_ladder_score is None
    assert ladder_report.reason_codes == ("no_claim_ladder_inputs",)
    assert ladder_report.reason_code_counts == (
        mod.ResearchSourceAuthorityMemoryClaimLadderReasonCodeCount(
            reason_code="no_claim_ladder_inputs",
            count=d("1"),
        ),
    )
    assert len(payload["public_payload_sha256"]) == 64


def test_custom_ladder_thresholds_drive_row_consistency() -> None:
    mod = module()

    ladder_report = report(
        mod,
        (
            claim(
                mod,
                1,
                authority_tier="secondary",
                observed_at=GENERATED_AT - timedelta(minutes=30),
                memory_confidence=d("1.000000"),
                corroboration_count=d("2"),
            ),
        ),
        cfg=config(
            mod,
            pass_ladder_score=d("0.600000"),
            watch_ladder_score=d("0.200000"),
        ),
    )

    row = ladder_report.rows[0]
    assert row.status == "pass"
    assert row.claim_ladder_score == d("0.700000")
    assert row.pass_ladder_score == d("0.600000")
    assert row.watch_ladder_score == d("0.200000")


def test_validation_rejects_bad_types_enums_times_status_and_flags() -> None:
    mod = module()

    with pytest.raises(ValueError, match="pass_ladder_score"):
        config(mod, pass_ladder_score=0.75)
    with pytest.raises(ValueError, match="memory_weight"):
        config(mod, memory_weight=_DecimalSubclass("0.300000"))
    with pytest.raises(ValueError, match="authority_weight"):
        config(mod, authority_weight=d("0.400000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(mod, (claim(mod, 1),), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            mod,
            (claim(mod, 1),),
            generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="claim_id"):
        claim(mod, 1, claim_id=" Claim Alpha")
    with pytest.raises(ValueError, match="authority_tier"):
        claim(mod, 1, authority_tier="message-board")
    with pytest.raises(ValueError, match="observed_at"):
        claim(mod, 1, observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        report(
            mod,
            (
                claim(
                    mod,
                    1,
                    observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )
    with pytest.raises(ValueError, match="memory_confidence"):
        claim(mod, 1, memory_confidence=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="corroboration_count"):
        claim(mod, 1, corroboration_count=d("1.5"))
    with pytest.raises(ValueError, match="reason_codes"):
        claim(mod, 1, reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(claim(mod, 1), paper_only=False)

    ladder_report = report(mod, (claim(mod, 1),))
    with pytest.raises(ValueError, match="status"):
        replace(ladder_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="status"):
        replace(ladder_report, status="blocked")


def test_public_dataclasses_are_frozen_exact_and_consistency_checked() -> None:
    mod = module()
    ladder_report = report(mod, (claim(mod, 1),))

    assert is_dataclass(mod.ResearchSourceAuthorityMemoryClaimLadderConfig)
    assert is_dataclass(mod.ResearchSourceAuthorityMemoryClaimLadderClaim)
    assert is_dataclass(mod.ResearchSourceAuthorityMemoryClaimLadderRow)
    assert is_dataclass(mod.ResearchSourceAuthorityMemoryClaimLadderReport)

    with pytest.raises(FrozenInstanceError):
        ladder_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        ladder_report.rows[0].claim_ladder_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="claim_ladder_score"):
        replace(ladder_report.rows[0], claim_ladder_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(ladder_report, status="watch")


def test_supplied_claim_shapes_are_accepted_and_public_payload_stays_report_only() -> None:
    mod = module()

    ladder_report = report(
        mod,
        (
            SuppliedClaimShape(
                claim_id="claim-supplied",
                private_candidate_reference="candidate-supplied-private",
                private_market_reference="market-supplied-private",
                private_source_reference="source-supplied-private",
                authority_tier="specialist",
                observed_at=GENERATED_AT - timedelta(minutes=5),
                memory_confidence=d("0.900000"),
                corroboration_count=d("3"),
            ),
        ),
    )
    payload = mod.research_source_authority_memory_claim_ladder_report_payload(
        ladder_report,
    )

    assert ladder_report.rows[0].status == "watch"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["candidate_ref_digest"].startswith("sha256:")
    assert "candidate-supplied-private" not in json.dumps(payload, sort_keys=True)


def test_rejects_duplicate_claim_ids_unsafe_public_text_and_tampered_export() -> None:
    mod = module()

    with pytest.raises(ValueError, match="unique by claim_id"):
        report(
            mod,
            (
                claim(mod, 1, claim_id="claim-duplicate"),
                claim(mod, 2, claim_id="claim-duplicate"),
            ),
        )
    with pytest.raises(ValueError, match="unsafe public text"):
        claim(mod, 1, claim_id="wallet_order_live_trade")
    with pytest.raises(ValueError, match="unsafe public text"):
        claim(mod, 1, reason_codes=("api_key",))

    tampered_text_report = report(mod, (claim(mod, 1),))
    object.__setattr__(
        tampered_text_report.rows[0],
        "claim_id",
        "contains_wallet_order_surface",
    )
    with pytest.raises(ValueError, match="unsafe public"):
        mod.research_source_authority_memory_claim_ladder_report_payload(
            tampered_text_report,
        )

    tampered_numeric_report = report(mod, (claim(mod, 1),))
    object.__setattr__(tampered_numeric_report.rows[0], "authority_score", 0.9)
    with pytest.raises(ValueError, match="numeric primitives"):
        mod.research_source_authority_memory_claim_ladder_report_payload(
            tampered_numeric_report,
        )


def test_owned_module_has_no_external_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_authority_memory_claim_ladder_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_patterns = (
        r"\brequests\b",
        r"\burllib\b",
        r"\bhttpx\b",
        r"\baiohttp\b",
        r"\bsocket\b",
        r"\bwebsocket\b",
        r"\bsqlite\b",
        r"\bsqlalchemy\b",
        r"\bpsycopg\b",
        r"\bmysql\b",
        r"\bpostgres\b",
        r"\bwallet\b",
        r"\bprivate_key\b",
        r"\bsecret\b",
        r"\bauthenticate\b",
        r"\bauthorization\b",
        r"\bcredential\b",
        r"\border\b",
        r"\blive[_ -]?trading\b",
        r"\btrade\b",
        r"\btrading\b",
        r"\bposition_size\b",
        r"\bsizing\b",
        r"\brecommendation\b",
        r"\bopen\(",
        r"\bconnect\(",
    )

    assert all(re.search(pattern, source) is None for pattern in forbidden_patterns)


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
