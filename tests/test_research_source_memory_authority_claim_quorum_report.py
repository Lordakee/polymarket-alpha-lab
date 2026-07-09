from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_source_memory_authority_claim_quorum_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_memory_authority_claim_quorum_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
FORBIDDEN_PUBLIC_FRAGMENTS = (
    "candidate-private",
    "market-private",
    "https://raw.example.test",
    "source url",
    "source text",
    "dsn=postgres",
    "memory_table",
    "token=secret",
    "private_candidate_ref",
    "private_market_ref",
    "private_locator_ref",
)


class DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    module = api()
    values = {
        "min_pass_claim_quorum_score": d("0.800000"),
        "min_watch_claim_quorum_score": d("0.550000"),
        "min_pass_authority_count": d("2.000000"),
        "min_pass_support_weight": d("2.000000"),
        "max_memory_age_seconds": d("86400.000000"),
        "watch_conflict_weight": d("0.250000"),
        "block_conflict_weight": d("0.700000"),
    }
    values.update(overrides)
    return module.ResearchSourceMemoryAuthorityClaimQuorumConfig(**values)


def item(
    index: int,
    *,
    claim_group: str = "claim-alpha",
    authority_group: str | None = None,
    observed_at: datetime | None = None,
    authority_weight: Decimal = d("1.000000"),
    memory_authority_score: Decimal = d("0.920000"),
    claim_support_score: Decimal = d("0.900000"),
    contradiction_weight: Decimal = d("0.000000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceMemoryAuthorityClaimQuorumInput(
        claim_group=claim_group,
        authority_group=authority_group or f"authority-{index:03d}",
        private_candidate_ref=f"candidate-private-{index}; token=secret-{index}",
        private_market_ref=(
            f"market-private-{index}; question=Will Alpha resolve {index}?"
        ),
        private_locator_ref=(
            "source URL https://raw.example.test/private?"
            f"dsn=postgres://user:pass@host/db&table=memory_table_{index}; "
            "source text"
        ),
        observed_at=observed_at
        if observed_at is not None
        else GENERATED_AT - timedelta(minutes=20),
        authority_weight=authority_weight,
        memory_authority_score=memory_authority_score,
        claim_support_score=claim_support_score,
        contradiction_weight=contradiction_weight,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    rows: tuple[Any, ...],
    *,
    config: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_source_memory_authority_claim_quorum_report(
        rows,
        config=config if config is not None else cfg(),
        generated_at=generated_at,
    )


def public_payload(report_or_payload: object) -> dict[str, object]:
    module = api()
    return module.research_source_memory_authority_claim_quorum_report_public_payload(
        report_or_payload,
    )


def walk_payload_values(value: object) -> list[object]:
    values: list[object] = [value]
    if type(value) is dict:
        for key, item_value in value.items():
            values.extend(walk_payload_values(key))
            values.extend(walk_payload_values(item_value))
    elif type(value) is list:
        for item_value in value:
            values.extend(walk_payload_values(item_value))
    return values


def assert_public_payload_is_decimal_string_only(payload: dict[str, object]) -> None:
    for value in walk_payload_values(payload):
        if type(value) in (int, float, Decimal):
            raise AssertionError(f"public payload leaked numeric scalar {value!r}")


def assert_no_public_raw_leaks(payload: dict[str, object]) -> None:
    encoded = json.dumps(payload, sort_keys=True).lower()
    for fragment in FORBIDDEN_PUBLIC_FRAGMENTS:
        assert fragment not in encoded


def assert_dataclass_decimal_only(value: object) -> None:
    assert is_dataclass(value)
    decimal_fields = {
        "min_pass_claim_quorum_score",
        "min_watch_claim_quorum_score",
        "min_pass_authority_count",
        "min_pass_support_weight",
        "max_memory_age_seconds",
        "watch_conflict_weight",
        "block_conflict_weight",
        "authority_weight",
        "memory_authority_score",
        "claim_support_score",
        "contradiction_weight",
        "evidence_count",
        "authority_count",
        "support_weight",
        "conflict_weight",
        "claim_quorum_score",
        "latest_age_seconds",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_claim_quorum_score",
        "minimum_claim_quorum_score",
    }
    for field in fields(value):
        field_value = getattr(value, field.name)
        if field.name in decimal_fields:
            assert type(field_value) is Decimal


def test_claim_quorum_report_scores_sorts_and_redacts_public_payload() -> None:
    module = api()
    report = build_report(
        (
            item(
                4,
                claim_group="gamma-block",
                observed_at=GENERATED_AT - timedelta(days=3),
                memory_authority_score=d("0.700000"),
                claim_support_score=d("0.700000"),
            ),
            item(
                1,
                claim_group="alpha-pass",
                authority_group="authority-official",
            ),
            item(
                2,
                claim_group="alpha-pass",
                authority_group="authority-archive",
                memory_authority_score=d("0.880000"),
                claim_support_score=d("0.860000"),
            ),
            item(
                3,
                claim_group="beta-watch",
                authority_group="authority-single",
                memory_authority_score=d("0.760000"),
                claim_support_score=d("0.700000"),
                contradiction_weight=d("0.300000"),
                reason_codes=("manual_followup",),
            ),
        ),
    )

    assert report.status == "block"
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_claim_quorum_score == d("0.520000")
    assert report.minimum_claim_quorum_score == d("0.000000")
    assert report.reason_codes == (
        "claim_quorum_block",
        "claim_quorum_memory_stale",
    )

    block_row, watch_row, pass_row = report.rows
    assert type(block_row) is module.ResearchSourceMemoryAuthorityClaimQuorumRow
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert block_row.claim_group == "gamma-block"
    assert block_row.claim_ref_digest.startswith("sha256:")
    assert block_row.locator_ref_digest.startswith("sha256:")
    assert block_row.latest_age_seconds == d("259200.000000")
    assert block_row.claim_quorum_score == d("0.000000")
    assert block_row.reason_codes == (
        "claim_quorum_block",
        "claim_quorum_memory_stale",
    )

    assert watch_row.status == "watch"
    assert watch_row.claim_quorum_score == d("0.700000")
    assert watch_row.conflict_weight == d("0.300000")
    assert watch_row.reason_codes == (
        "claim_quorum_conflict_watch",
        "claim_quorum_insufficient_authority",
        "claim_quorum_insufficient_weight",
        "claim_quorum_watch",
        "input_manual_followup",
    )

    assert pass_row.status == "pass"
    assert pass_row.evidence_count == d("2.000000")
    assert pass_row.authority_count == d("2.000000")
    assert pass_row.support_weight == d("2.000000")
    assert pass_row.claim_quorum_score == d("0.860000")
    assert pass_row.reason_codes == ("claim_quorum_pass",)

    payload = public_payload(report)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["row_count"] == "3.000000"
    assert payload["average_claim_quorum_score"] == "0.520000"
    assert payload["rows"][0]["claim_quorum_score"] == "0.000000"
    assert_public_payload_is_decimal_string_only(payload)
    assert_no_public_raw_leaks(payload)


def test_public_payload_is_deterministic_and_sha256_validated() -> None:
    module = api()
    first = build_report(
        (
            item(2, claim_group="alpha-pass", authority_group="authority-archive"),
            item(1, claim_group="alpha-pass", authority_group="authority-official"),
        ),
    )
    second = build_report(
        (
            item(1, claim_group="alpha-pass", authority_group="authority-official"),
            item(2, claim_group="alpha-pass", authority_group="authority-archive"),
        ),
    )

    first_payload = public_payload(first)
    second_payload = public_payload(second)

    assert first_payload == second_payload
    digest_material = {
        key: value
        for key, value in first_payload.items()
        if key != "derived_validation_digest"
    }
    expected_digest = hashlib.sha256(
        json.dumps(
            digest_material,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    assert first_payload["derived_validation_digest"] == expected_digest
    assert module.validate_research_source_memory_authority_claim_quorum_report_public_payload(
        first_payload,
    )

    tampered = dict(first_payload)
    tampered["status"] = "block"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        public_payload(tampered)

    unsafe = dict(first_payload)
    unsafe["leaked_note"] = "candidate-private token=secret source text"
    with pytest.raises(ValueError, match="unsafe public"):
        public_payload(unsafe)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    sample_config = cfg()
    sample_input = item(1)
    sample_report = build_report((sample_input,))
    sample_row = sample_report.rows[0]

    for sample in (sample_config, sample_input, sample_row, sample_report):
        assert_dataclass_decimal_only(sample)
        assert sample.paper_only is True
        assert sample.report_only is True
        assert sample.readonly is True
        with pytest.raises(FrozenInstanceError):
            sample.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        item(1, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        build_report((item(1, readonly=False),))


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        ("authority_weight", DecimalSubclass("1.000000"), "authority_weight"),
        ("memory_authority_score", d("1.000001"), "memory_authority_score"),
        ("claim_support_score", d("-0.000001"), "claim_support_score"),
        ("contradiction_weight", 0.1, "contradiction_weight"),
    ),
)
def test_rejects_non_decimal_or_out_of_range_numeric_inputs(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        item(1, **{field_name: bad_value})


def test_status_domain_and_empty_report_are_only_pass_watch_block() -> None:
    empty = build_report(())
    report = build_report(
        (
            item(1),
            item(2, claim_group="beta-watch", claim_support_score=d("0.600000")),
            item(3, claim_group="gamma-block", observed_at=GENERATED_AT - timedelta(days=3)),
        ),
    )

    assert empty.status == "block"
    assert empty.reason_codes == ("no_claim_quorum_inputs",)
    statuses = {empty.status, report.status}
    statuses.update(row.status for row in report.rows)
    assert statuses <= {"pass", "watch", "block"}
    assert "blocked" not in repr(report)


def test_module_has_no_db_network_wallet_auth_order_or_live_trading_surface() -> None:
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
        "web3",
    )
    forbidden_call_or_attribute_names = {
        "cancel",
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
        "persist",
        "recommend",
        "rollback",
        "send",
        "size",
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
