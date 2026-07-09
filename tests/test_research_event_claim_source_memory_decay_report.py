from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import importlib
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_event_claim_source_memory_decay_report"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode(
        "utf-8",
    )
    return hashlib.sha256(encoded).hexdigest()


def walk_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_payload_values(nested))
    if isinstance(value, list):
        return tuple(item for nested in value for item in walk_payload_values(nested))
    return (value,)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": (
            module.DEFAULT_RESEARCH_EVENT_CLAIM_SOURCE_MEMORY_DECAY_REPORT_CONFIG_VERSION
        ),
        "minimum_pass_source_count": d("3.000000"),
        "minimum_watch_source_count": d("2.000000"),
        "maximum_pass_average_age_hours": d("12.000000"),
        "maximum_watch_average_age_hours": d("48.000000"),
        "minimum_pass_average_quality_score": d("0.800000"),
        "minimum_watch_average_quality_score": d("0.500000"),
        "maximum_pass_conflict_ratio": d("0.000000"),
        "maximum_watch_conflict_ratio": d("0.250000"),
        "minimum_pass_memory_decay_score": d("0.750000"),
        "minimum_watch_memory_decay_score": d("0.450000"),
        "source_count_weight": d("0.200000"),
        "freshness_weight": d("0.400000"),
        "quality_weight": d("0.300000"),
        "conflict_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchEventClaimSourceMemoryDecayConfig(**values)


def claim_input(
    private_claim_ref: str = "private-claim-alpha",
    private_source_ref: str = "private-source-alpha",
    *,
    observed_at: datetime = datetime(2026, 7, 9, 10, 0, tzinfo=UTC),
    source_quality_score: Decimal = d("0.900000"),
    conflicts_with_claim: bool = False,
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchEventClaimSourceMemoryDecayInput(
        private_claim_ref=private_claim_ref,
        private_source_ref=private_source_ref,
        observed_at=observed_at,
        source_quality_score=source_quality_score,
        conflicts_with_claim=conflicts_with_claim,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg: object | None = None) -> Any:
    module = api()
    return module.build_research_event_claim_source_memory_decay_report(
        items,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def test_scores_event_claim_source_memory_decay_pass_watch_and_block_rows() -> None:
    module = api()
    built = report(
        claim_input(
            "pass-claim",
            "pass-source-a",
            observed_at=datetime(2026, 7, 9, 10, 0, tzinfo=UTC),
            source_quality_score=d("0.900000"),
        ),
        claim_input(
            "pass-claim",
            "pass-source-b",
            observed_at=datetime(2026, 7, 9, 8, 0, tzinfo=UTC),
            source_quality_score=d("0.800000"),
        ),
        claim_input(
            "pass-claim",
            "pass-source-c",
            observed_at=datetime(2026, 7, 9, 6, 0, tzinfo=UTC),
            source_quality_score=d("0.850000"),
        ),
        claim_input(
            "watch-claim",
            "watch-source-a",
            observed_at=datetime(2026, 7, 8, 16, 0, tzinfo=UTC),
            source_quality_score=d("0.650000"),
        ),
        claim_input(
            "watch-claim",
            "watch-source-b",
            observed_at=datetime(2026, 7, 8, 6, 0, tzinfo=UTC),
            source_quality_score=d("0.650000"),
        ),
        claim_input(
            "block-claim",
            "block-source-a",
            observed_at=datetime(2026, 7, 6, 12, 0, tzinfo=UTC),
            source_quality_score=d("0.300000"),
            conflicts_with_claim=True,
            reason_codes=("manual_conflict_review",),
        ),
    )

    assert type(built) is module.ResearchEventClaimSourceMemoryDecayReport
    assert module.EVENT_CLAIM_SOURCE_MEMORY_DECAY_STATUSES == ("pass", "watch", "block")
    assert built.generated_at == GENERATED_AT
    assert built.status == "block"
    assert built.input_count == d("6.000000")
    assert built.row_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.stale_claim_count == d("2.000000")
    assert built.low_quality_claim_count == d("2.000000")
    assert built.thin_source_claim_count == d("2.000000")
    assert built.conflicted_claim_count == d("1.000000")
    assert built.average_memory_decay_score == d("0.516667")

    block_row, watch_row, pass_row = built.rows
    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")
    assert block_row.source_count == d("1.000000")
    assert block_row.average_source_age_hours == d("72.000000")
    assert block_row.average_source_quality_score == d("0.300000")
    assert block_row.conflict_ratio == ONE
    assert block_row.memory_decay_score == ZERO
    assert "event_claim_source_memory_decay_status_block" in block_row.reason_codes
    assert "input_manual_conflict_review" in block_row.reason_codes

    assert watch_row.source_count == d("2.000000")
    assert watch_row.average_source_age_hours == d("25.000000")
    assert watch_row.average_source_quality_score == d("0.650000")
    assert watch_row.memory_decay_score == d("0.550000")
    assert "event_claim_source_memory_decay_status_watch" in watch_row.reason_codes

    assert pass_row.source_count == d("3.000000")
    assert pass_row.average_source_age_hours == d("4.000000")
    assert pass_row.average_source_quality_score == d("0.850000")
    assert pass_row.conflict_ratio == ZERO
    assert pass_row.memory_decay_score == ONE
    assert pass_row.reason_codes == (
        "event_claim_source_memory_decay_conflict_pass",
        "event_claim_source_memory_decay_freshness_pass",
        "event_claim_source_memory_decay_quality_pass",
        "event_claim_source_memory_decay_source_count_pass",
        "event_claim_source_memory_decay_status_pass",
    )


def test_public_payload_is_deterministic_sanitized_and_sha256_bound() -> None:
    module = api()
    first = report(
        claim_input(
            "raw-candidate/market-question https://example.test/source?token=secret",
            "source-url-text-dsn-table-token-wallet-order-live-trading-sizing-recommend",
            source_quality_score=d("0.900000"),
        ),
        claim_input(
            "raw-candidate/market-question https://example.test/source?token=secret",
            "second-private-source",
            observed_at=datetime(2026, 7, 9, 9, 0, tzinfo=UTC),
            source_quality_score=d("0.900000"),
        ),
    )
    second = report(
        claim_input(
            "raw-candidate/market-question https://example.test/source?token=secret",
            "second-private-source",
            observed_at=datetime(2026, 7, 9, 9, 0, tzinfo=UTC),
            source_quality_score=d("0.900000"),
        ),
        claim_input(
            "raw-candidate/market-question https://example.test/source?token=secret",
            "source-url-text-dsn-table-token-wallet-order-live-trading-sizing-recommend",
            source_quality_score=d("0.900000"),
        ),
    )

    payload = module.research_event_claim_source_memory_decay_report_payload(first)

    assert payload == second.public_payload
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["row_count"] == "1.000000"
    assert payload["rows"][0]["source_count"] == "2.000000"
    assert module.validate_research_event_claim_source_memory_decay_report_payload(
        payload,
    ) == payload

    rendered = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "raw-candidate",
        "market-question",
        "https://example.test",
        "token=secret",
        "private_claim_ref",
        "private_source_ref",
        "candidate",
        "market",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "live trading",
        "sizing",
        "recommend",
    ):
        assert forbidden not in rendered

    assert not any(isinstance(value, Decimal) for value in walk_payload_values(payload))
    assert not any(
        isinstance(value, (float, int)) and not isinstance(value, bool)
        for value in walk_payload_values(payload)
    )

    tampered = dict(payload)
    tampered["row_count"] = "999.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_event_claim_source_memory_decay_report_payload(tampered)

    unsafe = dict(payload)
    unsafe["source_url"] = "https://example.test/private"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.validate_research_event_claim_source_memory_decay_report_payload(unsafe)


def test_validation_rejects_bad_boundaries_types_statuses_and_flag_downgrades() -> None:
    module = api()

    with pytest.raises(ValueError, match="minimum_pass_source_count"):
        config(minimum_pass_source_count=DecimalSubclass("3.000000"))
    with pytest.raises(ValueError, match="minimum_watch_source_count"):
        config(minimum_watch_source_count=3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="minimum_pass_source_count"):
        config(minimum_pass_source_count=d("1.000000"))
    with pytest.raises(ValueError, match="maximum_pass_average_age_hours"):
        config(maximum_pass_average_age_hours=d("72.000000"))
    with pytest.raises(ValueError, match="minimum_pass_average_quality_score"):
        config(minimum_pass_average_quality_score=d("0.400000"))
    with pytest.raises(ValueError, match="maximum_pass_conflict_ratio"):
        config(maximum_pass_conflict_ratio=d("0.500000"))
    with pytest.raises(ValueError, match="weights must sum"):
        config(source_count_weight=d("0.210000"))
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)

    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_event_claim_source_memory_decay_report(
            (claim_input(),),
            config=config(),
            generated_at=datetime(2026, 7, 9, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_event_claim_source_memory_decay_report(
            (claim_input(),),
            config=config(),
            generated_at=DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        claim_input(observed_at=datetime(2026, 7, 9, 10, 0))
    with pytest.raises(ValueError, match="source_quality_score"):
        claim_input(source_quality_score=d("NaN"))
    with pytest.raises(ValueError, match="source_quality_score"):
        claim_input(source_quality_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_codes"):
        claim_input(reason_codes=("token_seen",))
    with pytest.raises(ValueError, match="readonly"):
        report(claim_input(readonly=False))
    with pytest.raises(ValueError, match="observed_at"):
        report(claim_input(observed_at=datetime(2026, 7, 9, 13, 0, tzinfo=UTC)))
    with pytest.raises(ValueError, match="private_source_ref"):
        report(
            claim_input("same-claim", "duplicate-source"),
            claim_input("same-claim", "duplicate-source"),
        )

    built = report(claim_input())
    with pytest.raises(ValueError, match="status"):
        replace(built.rows[0], status="blocked")
    with pytest.raises(ValueError, match="memory_decay_score"):
        replace(built.rows[0], memory_decay_score=ZERO)
    with pytest.raises(ValueError, match="status"):
        replace(built, status="watch")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="report"):
        module.research_event_claim_source_memory_decay_report_payload(object())


def test_public_objects_are_frozen_dataclasses_with_decimal_numeric_fields() -> None:
    module = api()
    built = report(claim_input())

    for item in (config(), claim_input(), built, *built.reason_code_counts, *built.rows):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True

    with pytest.raises(FrozenInstanceError):
        built.row_count = d("2.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].memory_decay_score = ZERO  # type: ignore[misc]

    public_classes = (
        module.ResearchEventClaimSourceMemoryDecayConfig,
        module.ResearchEventClaimSourceMemoryDecayInput,
        module.ResearchEventClaimSourceMemoryDecayRow,
        module.ResearchEventClaimSourceMemoryDecayReasonCodeCount,
        module.ResearchEventClaimSourceMemoryDecayReport,
    )
    for klass in public_classes:
        assert klass.__dataclass_params__.frozen is True
        for field in fields(klass):
            if field.name in {
                "paper_only",
                "report_only",
                "readonly",
                "private_claim_ref",
                "private_source_ref",
                "public_claim_ref",
                "config_version",
                "status",
                "reason_code",
                "reason_codes",
                "reason_code_counts",
                "rows",
                "derived_validation_digest",
                "observed_at",
                "generated_at",
                "conflicts_with_claim",
            }:
                continue
            assert field.type in (Decimal, "Decimal")


def test_owned_module_has_no_storage_network_wallet_execution_or_decision_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_event_claim_source_memory_decay_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    tree = ast.parse(module_path.read_text(encoding="utf-8"))

    for forbidden in (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "read_text",
        "write_text",
        "connect(",
        "execute(",
        "database",
        "db",
        "network",
        "wallet",
        "auth",
        "private_key",
        "api_key",
        "token",
        "order",
        "live trading",
        "sizing",
        "recommendation",
    ):
        assert forbidden not in source

    imported_roots = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert imported_roots <= {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
