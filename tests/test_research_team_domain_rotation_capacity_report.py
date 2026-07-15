from __future__ import annotations

import ast
import json
from collections.abc import Mapping, Sequence
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Context, Decimal, ROUND_DOWN, localcontext
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Any, get_type_hints

import pytest

from polymarket_alpha_lab.research_team_domain_rotation_capacity_report import (
    PUBLIC_STATUSES,
    REQUIRED_REVIEW_DOMAINS,
    ResearchTeamDomainRotationCapacityConfig,
    ResearchTeamDomainRotationCapacityObservation,
    ResearchTeamDomainRotationCapacityReasonCodeCount,
    ResearchTeamDomainRotationCapacityReport,
    ResearchTeamDomainRotationCapacityRow,
    build_research_team_domain_rotation_capacity_report,
    research_team_domain_rotation_capacity_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(minutes=5)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_team_domain_rotation_capacity_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    team_id: str,
    domain_id: str,
    *,
    observed_at: datetime = OBSERVED_AT,
    pending_review_count: Decimal = d("4.000000"),
    available_review_capacity: Decimal = d("10.000000"),
    stale_review_count: Decimal = d("0.000000"),
    calibration_score: Decimal = d("0.900000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchTeamDomainRotationCapacityObservation:
    return ResearchTeamDomainRotationCapacityObservation(
        team_id=team_id,
        domain_id=domain_id,
        observed_at=observed_at,
        pending_review_count=pending_review_count,
        available_review_capacity=available_review_capacity,
        stale_review_count=stale_review_count,
        calibration_score=calibration_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def all_domain_observations() -> tuple[ResearchTeamDomainRotationCapacityObservation, ...]:
    return (
        observation(
            "politics_review",
            "politics",
            pending_review_count=d("14.000000"),
            available_review_capacity=d("10.000000"),
            stale_review_count=d("5.000000"),
            calibration_score=d("0.480000"),
        ),
        observation(
            "crypto_review",
            "crypto",
            pending_review_count=d("9.000000"),
            available_review_capacity=d("10.000000"),
            stale_review_count=d("2.000000"),
            calibration_score=d("0.680000"),
        ),
        observation("equities_review", "equities"),
        observation("commodities_review", "commodities"),
        observation("football_review", "football"),
        observation("basketball_review", "basketball"),
        observation("generalist_review", "other"),
    )


def build(
    rows: tuple[ResearchTeamDomainRotationCapacityObservation, ...],
    *,
    generated_at: datetime = GENERATED_AT,
    config: ResearchTeamDomainRotationCapacityConfig | None = None,
) -> ResearchTeamDomainRotationCapacityReport:
    return build_research_team_domain_rotation_capacity_report(
        rows,
        generated_at=generated_at,
        config=config,
    )


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, Mapping):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(walk_values(item))
        return tuple(nested)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        nested = []
        for item in value:
            nested.extend(walk_values(item))
        return tuple(nested)
    return (value,)


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, Mapping):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            assert_no_float_values(item)


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    resigned = json.loads(json.dumps(payload))
    unsigned = dict(resigned)
    unsigned.pop("public_digest", None)
    encoded = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    resigned["public_digest"] = f"sha256:{sha256(encoded).hexdigest()}"
    return resigned


def mapping_sequence_contract(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType(
            {key: mapping_sequence_contract(item) for key, item in value.items()},
        )
    if isinstance(value, list):
        return tuple(mapping_sequence_contract(item) for item in value)
    return value


def assert_ast_has_no_forbidden_io(source_text: str) -> None:
    tree = ast.parse(source_text)
    forbidden_imports = {
        "aiohttp",
        "http",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    forbidden_calls = {
        "compile",
        "connect",
        "eval",
        "exec",
        "float",
        "open",
        "urlopen",
    }
    forbidden_methods = {
        "commit",
        "execute",
        "executemany",
        "persist",
        "request",
        "save",
        "send",
        "write",
        "write_bytes",
        "write_text",
    }
    importlib_aliases = {"importlib"}
    dynamic_import_names = {"__import__"}
    import_module_names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                assert root not in forbidden_imports
                if alias.name == "importlib":
                    importlib_aliases.add(alias.asname or alias.name)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            root = node.module.split(".")[0]
            assert root not in forbidden_imports
            if node.module == "importlib":
                for alias in node.names:
                    if alias.name == "import_module":
                        import_module_names.add(alias.asname or alias.name)

    assignments = tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.Assign, ast.AnnAssign))
    )
    changed = True
    while changed:
        changed = False
        for assignment in assignments:
            targets = (
                assignment.targets
                if isinstance(assignment, ast.Assign)
                else (assignment.target,)
            )
            value = assignment.value
            target_names = tuple(
                target.id for target in targets if isinstance(target, ast.Name)
            )
            if not target_names or value is None:
                continue
            if isinstance(value, ast.Name) and value.id in dynamic_import_names:
                for target_name in target_names:
                    if target_name not in dynamic_import_names:
                        dynamic_import_names.add(target_name)
                        changed = True
            if isinstance(value, ast.Name) and value.id in import_module_names:
                for target_name in target_names:
                    if target_name not in import_module_names:
                        import_module_names.add(target_name)
                        changed = True
            if (
                isinstance(value, ast.Attribute)
                and value.attr == "import_module"
                and isinstance(value.value, ast.Name)
                and value.value.id in importlib_aliases
            ):
                for target_name in target_names:
                    if target_name not in import_module_names:
                        import_module_names.add(target_name)
                        changed = True

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_calls
            assert node.func.id not in dynamic_import_names
            assert node.func.id not in import_module_names
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_methods
            assert not (
                node.func.attr == "import_module"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id in importlib_aliases
            )


def is_inside_fixed_decimal_context(
    node: ast.AST,
    parents: dict[ast.AST, ast.AST],
) -> bool:
    current = node
    while current in parents:
        current = parents[current]
        if not isinstance(current, ast.With):
            continue
        for item in current.items:
            expression = item.context_expr
            if (
                isinstance(expression, ast.Call)
                and isinstance(expression.func, ast.Name)
                and expression.func.id == "localcontext"
                and len(expression.args) == 1
                and isinstance(expression.args[0], ast.Name)
                and expression.args[0].id == "_DECIMAL_CONTEXT"
            ):
                return True
    return False


def test_domain_rotation_capacity_blocks_overloaded_stale_weak_team() -> None:
    report = build(
        all_domain_observations(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.report_status == "block"
    assert report.required_domain_count == d("7.000000")
    assert report.covered_domain_count == d("7.000000")
    assert report.team_domain_count == d("7.000000")
    assert report.pass_count == d("5.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.total_pending_review_count == d("43.000000")
    assert report.total_available_review_capacity == d("70.000000")
    assert report.total_capacity_shortfall_count == d("4.000000")
    assert report.weighted_capacity_utilization == d("0.614286")
    assert report.max_stale_review_ratio == d("0.357143")
    assert report.min_calibration_score == d("0.480000")
    assert report.average_calibration_score == d("0.808571")
    assert report.reason_codes == (
        "domain_rotation_capacity_block_present",
        "capacity_overloaded",
        "stale_rotation_block",
        "calibration_block",
        "capacity_near_limit",
        "stale_rotation_watch",
        "calibration_watch",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    blocked_row = report.rows[0]
    assert blocked_row.team_id == "politics_review"
    assert blocked_row.domain_id == "politics"
    assert blocked_row.observed_at == OBSERVED_AT
    assert blocked_row.observed_at.tzinfo is UTC
    assert blocked_row.status == "block"
    assert blocked_row.capacity_utilization == d("1.400000")
    assert blocked_row.capacity_shortfall_count == d("4.000000")
    assert blocked_row.stale_review_ratio == d("0.357143")
    assert blocked_row.calibration_gap_score == d("0.520000")
    assert blocked_row.reason_codes == (
        "capacity_overloaded",
        "stale_rotation_block",
        "calibration_block",
    )

    watch_row = report.rows[1]
    assert watch_row.team_id == "crypto_review"
    assert watch_row.status == "watch"
    assert watch_row.reason_codes == (
        "capacity_near_limit",
        "stale_rotation_watch",
        "calibration_watch",
    )


def test_observed_at_is_utc_and_bounded_by_report_as_of() -> None:
    shifted_observed_at = OBSERVED_AT.astimezone(timezone(timedelta(hours=-4)))
    report = build(
        (
            observation(
                "politics_review",
                "politics",
                observed_at=shifted_observed_at,
            ),
        ),
    )

    assert report.rows[0].observed_at == OBSERVED_AT
    assert report.rows[0].observed_at.tzinfo is UTC
    assert report.payload["rows"][0]["observed_at"] == OBSERVED_AT.isoformat()

    equal_to_as_of = build(
        (
            observation(
                "politics_review",
                "politics",
                observed_at=GENERATED_AT,
            ),
        ),
    )
    assert equal_to_as_of.rows[0].observed_at == GENERATED_AT

    with pytest.raises(ValueError, match="observed_at.*UTC-aware"):
        observation(
            "politics_review",
            "politics",
            observed_at=datetime(2026, 7, 8, 11, 55),
        )
    with pytest.raises(ValueError, match="observed_at.*datetime"):
        observation(
            "politics_review",
            "politics",
            observed_at=_DatetimeSubclass(2026, 7, 8, 11, 55, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at.*UTC-aware"):
        build(
            (observation("politics_review", "politics"),),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="observed_at.*future"):
        build(
            (
                observation(
                    "politics_review",
                    "politics",
                    observed_at=GENERATED_AT + timedelta(microseconds=1),
                ),
            ),
        )

    forged = json.loads(json.dumps(report.payload))
    forged["rows"][0]["observed_at"] = (
        GENERATED_AT + timedelta(microseconds=1)
    ).isoformat()
    with pytest.raises(ValueError, match="observed_at.*future"):
        research_team_domain_rotation_capacity_report_payload(
            resign_payload(forged),
        )


def test_pass_status_when_all_domains_have_clear_capacity_and_calibration() -> None:
    report = build(
        tuple(
            observation(f"{domain_id}_review", domain_id)
            for domain_id in REQUIRED_REVIEW_DOMAINS
        ),
    )

    assert report.report_status == "pass"
    assert report.pass_count == d("7.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.total_capacity_shortfall_count == d("0.000000")
    assert report.reason_codes == ("domain_rotation_capacity_clear",)
    assert all(row.status == "pass" for row in report.rows)


def test_missing_required_domain_is_watch_even_when_present_rows_pass() -> None:
    rows = tuple(
        observation(f"{domain_id}_review", domain_id)
        for domain_id in REQUIRED_REVIEW_DOMAINS
        if domain_id != "basketball"
    )

    report = build(rows)

    assert report.report_status == "watch"
    assert report.covered_domain_count == d("6.000000")
    assert report.missing_domain_count == d("1.000000")
    assert report.reason_codes == ("domain_rotation_capacity_missing_domain",)


def test_decimal_aggregates_and_digest_are_stable_under_hostile_context() -> None:
    rows = all_domain_observations()
    baseline = build(rows)

    with localcontext(Context(prec=2, rounding=ROUND_DOWN)):
        hostile = build(rows)
        hostile_payload = hostile.payload

    assert hostile_payload == baseline.payload
    assert hostile.public_digest == baseline.public_digest
    assert hostile.total_pending_review_count == d("43.000000")
    assert hostile.total_available_review_capacity == d("70.000000")
    assert hostile.average_calibration_score == d("0.808571")


def test_derived_subtraction_is_stable_under_hostile_decimal_context() -> None:
    item = observation(
        "politics_review",
        "politics",
        pending_review_count=d(
            "1000000000000000000000000000000000123456.000000",
        ),
        available_review_capacity=d(
            "1000000000000000000000000000000000000000.000000",
        ),
        calibration_score=d("0.123456"),
    )
    baseline = build((item,))

    with localcontext(Context(prec=2, rounding=ROUND_DOWN)):
        hostile = build((item,))

    assert hostile.rows[0].capacity_shortfall_count == d("123456.000000")
    assert hostile.rows[0].calibration_gap_score == d("0.876544")
    assert hostile.rows == baseline.rows
    assert hostile.public_digest == baseline.public_digest


def test_report_and_payload_rebuild_reject_duplicate_team_domain_rows() -> None:
    report = build(all_domain_observations())

    with pytest.raises(ValueError, match="duplicate team/domain"):
        replace(report, rows=(report.rows[0], report.rows[0]))

    forged = json.loads(json.dumps(report.payload))
    forged["rows"].append(forged["rows"][0])
    with pytest.raises(ValueError, match="duplicate team/domain"):
        research_team_domain_rotation_capacity_report_payload(
            resign_payload(forged),
        )


def test_missing_domain_ratio_uses_required_domains_and_row_reasons_use_rows() -> None:
    rows = tuple(
        observation(f"{domain_id}_review", domain_id)
        for domain_id in REQUIRED_REVIEW_DOMAINS
        if domain_id != "basketball"
    ) + (
        observation("politics_backup", "politics"),
        observation("equities_backup", "equities"),
    )

    report = build(rows)
    counts = {item.reason_code: item for item in report.reason_code_counts}

    missing = counts["domain_rotation_capacity_missing_domain"]
    clear = counts["domain_rotation_capacity_clear"]
    assert missing.count == d("1.000000")
    assert missing.domain_ratio == d("0.142857")
    assert clear.count == d("8.000000")
    assert clear.domain_ratio == d("1.000000")


def test_row_sort_key_has_a_total_team_domain_tie_break() -> None:
    rows = (
        observation("politics_b", "politics"),
        observation("crypto_z", "crypto"),
        observation("politics_a", "politics"),
    )

    first = build(rows)
    second = build(tuple(reversed(rows)))

    expected = (
        ("crypto_z", "crypto"),
        ("politics_a", "politics"),
        ("politics_b", "politics"),
    )
    assert tuple((row.team_id, row.domain_id) for row in first.rows) == expected
    assert first.rows == second.rows
    assert first.public_digest == second.public_digest


def test_row_sort_key_applies_every_priority_and_final_tie_break() -> None:
    rows = (
        observation(
            "pass_row",
            "basketball",
            pending_review_count=d("4.000000"),
            available_review_capacity=d("10.000000"),
        ),
        observation(
            "block_politics_b",
            "politics",
            pending_review_count=d("10.000000"),
            available_review_capacity=d("10.000000"),
            stale_review_count=d("3.000000"),
            calibration_score=d("0.400000"),
        ),
        observation(
            "block_capacity_high",
            "other",
            pending_review_count=d("12.000000"),
            available_review_capacity=d("10.000000"),
        ),
        observation(
            "block_calibration_low",
            "commodities",
            pending_review_count=d("10.000000"),
            available_review_capacity=d("10.000000"),
            stale_review_count=d("3.000000"),
            calibration_score=d("0.300000"),
        ),
        observation(
            "watch_row",
            "football",
            pending_review_count=d("9.000000"),
            available_review_capacity=d("10.000000"),
        ),
        observation(
            "block_stale_high",
            "equities",
            pending_review_count=d("10.000000"),
            available_review_capacity=d("10.000000"),
            stale_review_count=d("4.000000"),
            calibration_score=d("0.400000"),
        ),
        observation(
            "block_crypto",
            "crypto",
            pending_review_count=d("10.000000"),
            available_review_capacity=d("10.000000"),
            stale_review_count=d("3.000000"),
            calibration_score=d("0.400000"),
        ),
        observation(
            "block_politics_a",
            "politics",
            pending_review_count=d("10.000000"),
            available_review_capacity=d("10.000000"),
            stale_review_count=d("3.000000"),
            calibration_score=d("0.400000"),
        ),
    )

    first = build(rows)
    second = build(tuple(reversed(rows)))

    assert tuple(row.team_id for row in first.rows) == (
        "block_capacity_high",
        "block_stale_high",
        "block_calibration_low",
        "block_crypto",
        "block_politics_a",
        "block_politics_b",
        "watch_row",
        "pass_row",
    )
    assert first.rows == second.rows
    assert first.public_digest == second.public_digest


def test_standalone_row_rejects_noncanonical_reason_code_order() -> None:
    blocked_row = build(all_domain_observations()).rows[0]

    with pytest.raises(ValueError, match="reason_codes.*canonical order"):
        replace(
            blocked_row,
            reason_codes=tuple(reversed(blocked_row.reason_codes)),
        )


def test_empty_report_has_complete_canonical_derived_fields() -> None:
    report = build(())

    assert report.report_status == "watch"
    assert report.required_domain_count == d("7.000000")
    assert report.covered_domain_count == d("0.000000")
    assert report.missing_domain_count == d("7.000000")
    assert report.team_domain_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.total_pending_review_count == d("0.000000")
    assert report.total_available_review_capacity == d("0.000000")
    assert report.total_capacity_shortfall_count == d("0.000000")
    assert report.weighted_capacity_utilization == d("0.000000")
    assert report.max_stale_review_ratio == d("0.000000")
    assert report.min_calibration_score == d("0.000000")
    assert report.average_calibration_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("domain_rotation_capacity_missing_domain",)
    assert report.reason_code_counts == (
        ResearchTeamDomainRotationCapacityReasonCodeCount(
            reason_code="domain_rotation_capacity_missing_domain",
            count=d("7.000000"),
            domain_ratio=d("1.000000"),
        ),
    )
    assert research_team_domain_rotation_capacity_report_payload(
        mapping_sequence_contract(json.loads(json.dumps(report.payload))),
    ) == report.payload


def test_payload_is_public_safe_decimal_string_serialized_and_digest_validated() -> None:
    first = build(all_domain_observations())
    second = build(tuple(reversed(all_domain_observations())))

    payload = research_team_domain_rotation_capacity_report_payload(first)
    encoded = json.dumps(payload, sort_keys=True)

    assert first.payload == payload
    assert first.public_digest == second.public_digest
    assert payload["public_digest"] == first.public_digest
    assert payload["public_digest"].startswith("sha256:")
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["weighted_capacity_utilization"] == "0.614286"
    assert payload["rows"][0]["capacity_shortfall_count"] == "4.000000"
    assert payload["rows"][0]["reason_codes"] == [
        "capacity_overloaded",
        "stale_rotation_block",
        "calibration_block",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert '"0.614286"' in encoded
    assert_no_float_values(payload)

    public_strings = tuple(value for value in walk_values(payload) if type(value) is str)
    forbidden_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "postgres://",
        "table:",
        "token=",
        "wallet",
        "order_id",
        "trade_id",
    )
    assert not any(
        fragment in item.lower()
        for fragment in forbidden_fragments
        for item in public_strings
    )

    with pytest.raises(ValueError, match="public_digest must match report payload"):
        replace(first, public_digest="sha256:" + ("0" * 64))


def test_public_payload_is_recursively_readonly() -> None:
    mutators = (
        lambda payload: payload.__setitem__("report_status", "pass"),
        lambda payload: payload["config"].__setitem__(
            "config_version",
            "changed",
        ),
        lambda payload: payload["rows"].append(payload["rows"][0]),
        lambda payload: payload["rows"][0].__setitem__("status", "pass"),
        lambda payload: payload["rows"][0]["reason_codes"].append(
            "domain_rotation_capacity_clear",
        ),
        lambda payload: payload["reason_code_counts"][0].__setitem__(
            "count",
            "0.000000",
        ),
    )

    for mutate in mutators:
        with pytest.raises(TypeError, match="immutable"):
            mutate(build(all_domain_observations()).payload)


def test_payload_validator_accepts_mapping_and_sequence_contracts() -> None:
    mutable = json.loads(json.dumps(build(all_domain_observations()).payload))
    contract_payload = mapping_sequence_contract(mutable)

    validated = research_team_domain_rotation_capacity_report_payload(
        contract_payload,
    )

    assert isinstance(validated, Mapping)
    assert isinstance(validated["rows"], Sequence)
    assert validated == mutable
    with pytest.raises(TypeError, match="immutable"):
        validated["rows"].append(validated["rows"][0])


@pytest.mark.parametrize("target_name", ("report", "config", "row", "reason_count"))
def test_payload_rejects_nonexact_json_string_keys(target_name: str) -> None:
    payload = json.loads(json.dumps(build(all_domain_observations()).payload))

    if target_name == "report":
        target = payload
    elif target_name == "config":
        target = payload["config"]
    elif target_name == "row":
        target = payload["rows"][0]
    else:
        target = payload["reason_code_counts"][0]
    first_key = next(iter(target))
    forged_target = {
        (_StringSubclass(key) if key == first_key else key): value
        for key, value in target.items()
    }
    if target_name == "report":
        forged: Mapping[str, Any] = forged_target
    else:
        if target_name == "config":
            payload["config"] = forged_target
        elif target_name == "row":
            payload["rows"][0] = forged_target
        else:
            payload["reason_code_counts"][0] = forged_target
        forged = payload

    with pytest.raises(ValueError, match="JSON object keys must be strings"):
        research_team_domain_rotation_capacity_report_payload(forged)


@pytest.mark.parametrize(
    ("target_name", "label"),
    (
        ("report", "report payload"),
        ("config", "config payload"),
        ("row", "row payload"),
        ("reason_count", "reason code count payload"),
    ),
)
@pytest.mark.parametrize("mutation", ("missing", "unknown", "type", "reorder"))
def test_payload_requires_canonical_schema_order_and_types(
    target_name: str,
    label: str,
    mutation: str,
) -> None:
    payload = json.loads(json.dumps(build(all_domain_observations()).payload))

    if target_name == "report":
        target = payload
    elif target_name == "config":
        target = payload["config"]
    elif target_name == "row":
        target = payload["rows"][0]
    else:
        target = payload["reason_code_counts"][0]

    if mutation == "type":
        if target_name == "report":
            forged: Any = list(payload.items())
        elif target_name == "config":
            payload["config"] = []
            forged = resign_payload(payload)
        elif target_name == "row":
            payload["rows"][0] = []
            forged = resign_payload(payload)
        else:
            payload["reason_code_counts"][0] = []
            forged = resign_payload(payload)
    else:
        if mutation == "missing":
            target.pop(next(iter(target)))
        elif mutation == "unknown":
            target["unknown_field"] = "public"
        else:
            reordered = dict(reversed(tuple(target.items())))
            if target_name == "report":
                payload = reordered
            elif target_name == "config":
                payload["config"] = reordered
            elif target_name == "row":
                payload["rows"][0] = reordered
            else:
                payload["reason_code_counts"][0] = reordered
        forged = resign_payload(payload)

    with pytest.raises(ValueError, match=label):
        research_team_domain_rotation_capacity_report_payload(forged)


def test_payload_rejects_resigned_forged_derived_row_semantics() -> None:
    payload = build(all_domain_observations()).payload

    for field_name, forged_value in (
        ("capacity_utilization", "0.123456"),
        ("capacity_shortfall_count", "0.123456"),
        ("stale_review_ratio", "0.123456"),
        ("calibration_gap_score", "0.123456"),
    ):
        forged = json.loads(json.dumps(payload))
        forged["rows"][0][field_name] = forged_value
        with pytest.raises(ValueError, match=field_name):
            research_team_domain_rotation_capacity_report_payload(
                resign_payload(forged),
            )

    forged_policy = json.loads(json.dumps(payload))
    forged_policy["rows"][2]["status"] = "watch"
    forged_policy["rows"][2]["reason_codes"] = ["capacity_near_limit"]
    forged_policy["pass_count"] = "4.000000"
    forged_policy["watch_count"] = "2.000000"
    for reason_count in forged_policy["reason_code_counts"]:
        if reason_count["reason_code"] == "capacity_near_limit":
            reason_count["count"] = "2.000000"
            reason_count["domain_ratio"] = "0.285714"
            break
    with pytest.raises(ValueError, match="status|reason_codes"):
        research_team_domain_rotation_capacity_report_payload(
            resign_payload(forged_policy),
        )


@pytest.mark.parametrize(
    ("field_name", "forged_value"),
    (
        ("config_version", "research_team_domain_rotation_capacity_report.forged.v1"),
        ("report_status", "watch"),
        ("required_domain_count", "6.000000"),
        ("covered_domain_count", "6.000000"),
        ("missing_domain_count", "1.000000"),
        ("team_domain_count", "6.000000"),
        ("pass_count", "6.000000"),
        ("watch_count", "2.000000"),
        ("block_count", "2.000000"),
        ("total_pending_review_count", "42.000000"),
        ("total_available_review_capacity", "69.000000"),
        ("total_capacity_shortfall_count", "3.000000"),
        ("weighted_capacity_utilization", "0.123456"),
        ("max_stale_review_ratio", "0.123456"),
        ("min_calibration_score", "0.123456"),
        ("average_calibration_score", "0.123456"),
    ),
)
def test_payload_rejects_resigned_forged_report_derived_scalars(
    field_name: str,
    forged_value: str,
) -> None:
    forged = json.loads(json.dumps(build(all_domain_observations()).payload))
    forged[field_name] = forged_value

    with pytest.raises(ValueError, match=field_name):
        research_team_domain_rotation_capacity_report_payload(
            resign_payload(forged),
        )


def test_payload_rejects_resigned_forged_report_reasons_and_reason_counts() -> None:
    payload = build(all_domain_observations()).payload

    forged_reasons = json.loads(json.dumps(payload))
    forged_reasons["reason_codes"] = ["domain_rotation_capacity_clear"]
    with pytest.raises(ValueError, match="reason_codes"):
        research_team_domain_rotation_capacity_report_payload(
            resign_payload(forged_reasons),
        )

    forged_reason_counts = json.loads(json.dumps(payload))
    forged_reason_counts["reason_code_counts"][0]["count"] = "2.000000"
    forged_reason_counts["reason_code_counts"][0]["domain_ratio"] = "0.285714"
    with pytest.raises(ValueError, match="reason_code_counts"):
        research_team_domain_rotation_capacity_report_payload(
            resign_payload(forged_reason_counts),
        )


def test_payload_requires_exact_nested_schemas_even_when_resigned() -> None:
    payload = build(all_domain_observations()).payload

    assert tuple(payload) == tuple(
        item.name for item in fields(ResearchTeamDomainRotationCapacityReport)
    )
    assert tuple(payload["config"]) == tuple(
        item.name for item in fields(ResearchTeamDomainRotationCapacityConfig)
    )
    assert tuple(payload["rows"][0]) == tuple(
        item.name for item in fields(ResearchTeamDomainRotationCapacityRow)
    )
    assert tuple(payload["reason_code_counts"][0]) == tuple(
        item.name
        for item in fields(ResearchTeamDomainRotationCapacityReasonCodeCount)
    )

    forged_report = json.loads(json.dumps(payload))
    forged_report["extra"] = "public"
    with pytest.raises(ValueError, match="report payload.*exact schema"):
        research_team_domain_rotation_capacity_report_payload(
            resign_payload(forged_report),
        )

    forged_row = json.loads(json.dumps(payload))
    forged_row["rows"][0]["extra"] = "public"
    with pytest.raises(ValueError, match="row payload.*exact schema"):
        research_team_domain_rotation_capacity_report_payload(
            resign_payload(forged_row),
        )

    forged_config = json.loads(json.dumps(payload))
    forged_config["config"]["extra"] = "public"
    with pytest.raises(ValueError, match="config payload.*exact schema"):
        research_team_domain_rotation_capacity_report_payload(
            resign_payload(forged_config),
        )

    forged_reason_count = json.loads(json.dumps(payload))
    forged_reason_count["reason_code_counts"][0]["extra"] = "public"
    with pytest.raises(ValueError, match="reason code count payload.*exact schema"):
        research_team_domain_rotation_capacity_report_payload(
            resign_payload(forged_reason_count),
        )


def test_decimal_validation_uses_raw_bounds_and_rejects_signed_zero() -> None:
    with pytest.raises(ValueError, match="watch_capacity_utilization.*between 0 and 1"):
        ResearchTeamDomainRotationCapacityConfig(
            watch_capacity_utilization=d("1.0000001"),
        )
    with pytest.raises(ValueError, match="watch_capacity_utilization.*between 0 and 1"):
        ResearchTeamDomainRotationCapacityConfig(
            watch_capacity_utilization=d("-0.0000001"),
        )
    with pytest.raises(ValueError, match="pending_review_count.*nonnegative"):
        observation(
            "politics_review",
            "politics",
            pending_review_count=d("-0.0000001"),
        )
    with pytest.raises(ValueError, match="pending_review_count.*signed zero"):
        observation(
            "politics_review",
            "politics",
            pending_review_count=d("-0.000000"),
        )

    payload = build(all_domain_observations()).payload
    forged_signed_zero = json.loads(json.dumps(payload))
    forged_signed_zero["watch_count"] = "-0.000000"
    with pytest.raises(ValueError, match="watch_count.*signed zero"):
        research_team_domain_rotation_capacity_report_payload(
            resign_payload(forged_signed_zero),
        )

    forged_noncanonical = json.loads(json.dumps(payload))
    forged_noncanonical["watch_count"] = "1"
    with pytest.raises(ValueError, match="watch_count.*canonical Decimal string"):
        research_team_domain_rotation_capacity_report_payload(
            resign_payload(forged_noncanonical),
        )


def test_builder_revalidates_config_mutated_through_object_setattr() -> None:
    config = ResearchTeamDomainRotationCapacityConfig()
    object.__setattr__(
        config,
        "watch_capacity_utilization",
        d("-0.000001"),
    )

    with pytest.raises(ValueError, match="watch_capacity_utilization.*between 0 and 1"):
        build(all_domain_observations(), config=config)


def test_builder_revalidates_observation_mutated_through_object_setattr() -> None:
    item = observation("politics_review", "politics")
    object.__setattr__(item, "calibration_score", Decimal("NaN"))

    with pytest.raises(ValueError, match="calibration_score.*finite"):
        build((item,))


def test_report_revalidates_nested_row_mutated_through_object_setattr() -> None:
    report = build(all_domain_observations())
    row = report.rows[0]
    object.__setattr__(row, "status", "invalid")

    with pytest.raises(ValueError, match="status"):
        replace(report, rows=report.rows)


def test_report_payload_rejects_object_setattr_resigned_row_reordering() -> None:
    report = build(
        tuple(
            observation(f"{domain_id}_review", domain_id)
            for domain_id in REQUIRED_REVIEW_DOMAINS
        ),
    )
    forged = json.loads(json.dumps(report.payload))
    forged["rows"].reverse()
    resigned = resign_payload(forged)
    object.__setattr__(report, "rows", tuple(reversed(report.rows)))
    object.__setattr__(report, "public_digest", resigned["public_digest"])

    with pytest.raises(ValueError, match="canonical schema values"):
        research_team_domain_rotation_capacity_report_payload(report)


def test_report_payload_revalidates_mutated_nested_config_before_policy_checks() -> None:
    report = build(all_domain_observations())
    object.__setattr__(
        report.config,
        "watch_capacity_utilization",
        Decimal("NaN"),
    )

    with pytest.raises(ValueError, match="watch_capacity_utilization.*finite"):
        research_team_domain_rotation_capacity_report_payload(report)


def test_report_payload_rejects_nested_hard_flag_tampering() -> None:
    for target_name in ("config", "row", "reason_count"):
        for flag_name in ("paper_only", "report_only", "readonly"):
            report = build(all_domain_observations())
            if target_name == "config":
                target = report.config
            elif target_name == "row":
                target = report.rows[0]
            else:
                target = report.reason_code_counts[0]
            object.__setattr__(target, flag_name, False)

            with pytest.raises(ValueError, match=rf"{flag_name} must be True"):
                research_team_domain_rotation_capacity_report_payload(report)


def test_report_revalidates_reason_count_mutated_through_object_setattr() -> None:
    report = build(all_domain_observations())
    reason_count = report.reason_code_counts[0]
    object.__setattr__(
        reason_count,
        "reason_code",
        _StringSubclass(reason_count.reason_code),
    )

    with pytest.raises(ValueError, match="reason_code"):
        replace(report, reason_code_counts=report.reason_code_counts)


def test_custom_config_is_in_payload_and_revalidated_after_resigning() -> None:
    strict = ResearchTeamDomainRotationCapacityConfig(
        config_version="research_team_domain_rotation_capacity_report.strict.v1",
        watch_capacity_utilization=d("0.300000"),
        block_capacity_utilization=d("0.800000"),
    )
    report = build(
        tuple(
            observation(f"{domain_id}_review", domain_id)
            for domain_id in REQUIRED_REVIEW_DOMAINS
        ),
        config=strict,
    )
    payload = report.payload

    assert report.config == strict
    assert payload["config"]["config_version"] == strict.config_version
    assert payload["config"]["watch_capacity_utilization"] == "0.300000"
    assert payload["config"]["block_capacity_utilization"] == "0.800000"
    assert report.report_status == "watch"

    forged = json.loads(json.dumps(payload))
    forged["config"]["watch_capacity_utilization"] = "0.500000"
    with pytest.raises(ValueError, match="status|reason_codes"):
        research_team_domain_rotation_capacity_report_payload(
            resign_payload(forged),
        )


@pytest.mark.parametrize(
    (
        "field_name",
        "base_value",
        "config_overrides",
        "observation_overrides",
        "expected",
    ),
    (
        (
            "watch_capacity_utilization",
            d("0.600000"),
            {"block_capacity_utilization": d("1.000000")},
            {
                "pending_review_count": d("3.000000"),
                "available_review_capacity": d("5.000000"),
            },
            (
                ("watch", ("capacity_near_limit",)),
                ("watch", ("capacity_near_limit",)),
                ("pass", ("domain_rotation_capacity_clear",)),
            ),
        ),
        (
            "block_capacity_utilization",
            d("0.600000"),
            {"watch_capacity_utilization": d("0.500000")},
            {
                "pending_review_count": d("3.000000"),
                "available_review_capacity": d("5.000000"),
            },
            (
                ("block", ("capacity_overloaded",)),
                ("block", ("capacity_overloaded",)),
                ("watch", ("capacity_near_limit",)),
            ),
        ),
        (
            "watch_stale_review_ratio",
            d("0.200000"),
            {"block_stale_review_ratio": d("0.800000")},
            {
                "pending_review_count": d("5.000000"),
                "available_review_capacity": d("10.000000"),
                "stale_review_count": d("1.000000"),
            },
            (
                ("watch", ("stale_rotation_watch",)),
                ("watch", ("stale_rotation_watch",)),
                ("pass", ("domain_rotation_capacity_clear",)),
            ),
        ),
        (
            "block_stale_review_ratio",
            d("0.200000"),
            {"watch_stale_review_ratio": d("0.100000")},
            {
                "pending_review_count": d("5.000000"),
                "available_review_capacity": d("10.000000"),
                "stale_review_count": d("1.000000"),
            },
            (
                ("block", ("stale_rotation_block",)),
                ("block", ("stale_rotation_block",)),
                ("watch", ("stale_rotation_watch",)),
            ),
        ),
        (
            "watch_min_calibration_score",
            d("0.700000"),
            {"block_min_calibration_score": d("0.100000")},
            {"calibration_score": d("0.700000")},
            (
                ("pass", ("domain_rotation_capacity_clear",)),
                ("watch", ("calibration_watch",)),
                ("watch", ("calibration_watch",)),
            ),
        ),
        (
            "block_min_calibration_score",
            d("0.500000"),
            {"watch_min_calibration_score": d("0.800000")},
            {"calibration_score": d("0.500000")},
            (
                ("watch", ("calibration_watch",)),
                ("block", ("calibration_block",)),
                ("block", ("calibration_block",)),
            ),
        ),
    ),
)
def test_each_threshold_at_equal_and_plus_minus_one_quantum(
    field_name: str,
    base_value: Decimal,
    config_overrides: dict[str, Decimal],
    observation_overrides: dict[str, Decimal],
    expected: tuple[tuple[str, tuple[str, ...]], ...],
) -> None:
    quantum = d("0.000001")
    deltas = (-quantum, d("0.000000"), quantum)

    for delta, (expected_status, expected_reasons) in zip(deltas, expected):
        config = ResearchTeamDomainRotationCapacityConfig(
            **config_overrides,
            **{field_name: base_value + delta},
        )
        row = build(
            (
                observation(
                    "threshold_review",
                    "politics",
                    **observation_overrides,
                ),
            ),
            config=config,
        ).rows[0]
        assert row.status == expected_status
        assert row.reason_codes == expected_reasons


def test_public_dataclasses_are_frozen_and_use_exact_field_schemas() -> None:
    report = build(all_domain_observations())
    instances = (
        ResearchTeamDomainRotationCapacityConfig(),
        all_domain_observations()[0],
        report.rows[0],
        report.reason_code_counts[0],
        report,
    )
    expected_fields = {
        ResearchTeamDomainRotationCapacityConfig: (
            "config_version",
            "watch_capacity_utilization",
            "block_capacity_utilization",
            "watch_stale_review_ratio",
            "block_stale_review_ratio",
            "watch_min_calibration_score",
            "block_min_calibration_score",
            "paper_only",
            "report_only",
            "readonly",
        ),
        ResearchTeamDomainRotationCapacityObservation: (
            "team_id",
            "domain_id",
            "observed_at",
            "pending_review_count",
            "available_review_capacity",
            "stale_review_count",
            "calibration_score",
            "paper_only",
            "report_only",
            "readonly",
        ),
        ResearchTeamDomainRotationCapacityRow: (
            "team_id",
            "domain_id",
            "observed_at",
            "pending_review_count",
            "available_review_capacity",
            "stale_review_count",
            "calibration_score",
            "capacity_utilization",
            "capacity_shortfall_count",
            "stale_review_ratio",
            "calibration_gap_score",
            "status",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        ),
        ResearchTeamDomainRotationCapacityReasonCodeCount: (
            "reason_code",
            "count",
            "domain_ratio",
            "paper_only",
            "report_only",
            "readonly",
        ),
        ResearchTeamDomainRotationCapacityReport: (
            "generated_at",
            "config_version",
            "config",
            "report_status",
            "required_domain_count",
            "covered_domain_count",
            "missing_domain_count",
            "team_domain_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_pending_review_count",
            "total_available_review_capacity",
            "total_capacity_shortfall_count",
            "weighted_capacity_utilization",
            "max_stale_review_ratio",
            "min_calibration_score",
            "average_calibration_score",
            "rows",
            "reason_code_counts",
            "reason_codes",
            "public_digest",
            "paper_only",
            "report_only",
            "readonly",
        ),
    }

    for value in instances:
        cls = type(value)
        assert is_dataclass(value)
        assert cls.__dataclass_params__.frozen is True
        assert tuple(item.name for item in fields(cls)) == expected_fields[cls]
        with pytest.raises(FrozenInstanceError):
            setattr(value, fields(cls)[0].name, getattr(value, fields(cls)[0].name))


def test_public_dataclasses_are_final() -> None:
    classes = (
        ResearchTeamDomainRotationCapacityConfig,
        ResearchTeamDomainRotationCapacityObservation,
        ResearchTeamDomainRotationCapacityRow,
        ResearchTeamDomainRotationCapacityReasonCodeCount,
        ResearchTeamDomainRotationCapacityReport,
    )

    for cls in classes:
        assert getattr(cls, "__final__", False) is True
        assert tuple(cls.__slots__) == tuple(item.name for item in fields(cls))
        assert "__dict__" not in cls.__slots__
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Derived{cls.__name__}", (cls,), {})


def test_validation_rejects_bad_domains_types_precision_sensitive_values_and_flags() -> None:
    assert PUBLIC_STATUSES == ("pass", "watch", "block")
    assert REQUIRED_REVIEW_DOMAINS == (
        "politics",
        "crypto",
        "equities",
        "commodities",
        "football",
        "basketball",
        "other",
    )

    with pytest.raises(ValueError, match="team_id"):
        observation(_StringSubclass("politics_review"), "politics")

    with pytest.raises(ValueError, match="domain_id must be one of"):
        observation("baseball_review", "baseball")

    with pytest.raises(ValueError, match="pending_review_count must be a Decimal"):
        observation("politics_review", "politics", pending_review_count=4)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="calibration_score must be a Decimal"):
        observation(
            "politics_review",
            "politics",
            calibration_score=_DecimalSubclass("0.900000"),
        )

    with pytest.raises(ValueError, match="available_review_capacity must be positive"):
        observation(
            "politics_review",
            "politics",
            available_review_capacity=d("0.000000"),
        )

    with pytest.raises(ValueError, match="stale_review_count cannot exceed"):
        observation(
            "politics_review",
            "politics",
            pending_review_count=d("2.000000"),
            stale_review_count=d("3.000000"),
        )

    with pytest.raises(ValueError, match="required decimal precision"):
        observation(
            "politics_review",
            "politics",
            calibration_score=d("0.3333333"),
        )

    with pytest.raises(ValueError, match="must not expose restricted public material"):
        observation("wallet_rotation", "politics")

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(observation("politics_review", "politics"), paper_only=False)

    with pytest.raises(FrozenInstanceError):
        report = build(all_domain_observations())
        report.report_status = "watch"  # type: ignore[misc]


def test_public_numeric_dataclass_fields_are_decimal_only() -> None:
    numeric_fields = {
        "watch_capacity_utilization",
        "block_capacity_utilization",
        "watch_stale_review_ratio",
        "block_stale_review_ratio",
        "watch_min_calibration_score",
        "block_min_calibration_score",
        "pending_review_count",
        "available_review_capacity",
        "stale_review_count",
        "calibration_score",
        "capacity_utilization",
        "capacity_shortfall_count",
        "stale_review_ratio",
        "calibration_gap_score",
        "count",
        "domain_ratio",
        "required_domain_count",
        "covered_domain_count",
        "missing_domain_count",
        "team_domain_count",
        "pass_count",
        "watch_count",
        "block_count",
        "total_pending_review_count",
        "total_available_review_capacity",
        "total_capacity_shortfall_count",
        "weighted_capacity_utilization",
        "max_stale_review_ratio",
        "min_calibration_score",
        "average_calibration_score",
    }

    module_classes = (
        ResearchTeamDomainRotationCapacityConfig,
        ResearchTeamDomainRotationCapacityObservation,
        build(all_domain_observations()).rows[0].__class__,
        build(all_domain_observations()).reason_code_counts[0].__class__,
        ResearchTeamDomainRotationCapacityReport,
    )
    for cls in module_classes:
        hints = get_type_hints(cls)
        for item in fields(cls):
            if item.name in numeric_fields:
                assert hints[item.name] is Decimal


def test_sum_average_and_division_arithmetic_use_fixed_decimal_context() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    divisions = tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)
    )
    assert divisions
    assert all(is_inside_fixed_decimal_context(node, parents) for node in divisions)
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "sum"
        for node in ast.walk(tree)
    )

    sum_function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_sum_decimal"
    )
    sum_additions = tuple(
        node
        for node in ast.walk(sum_function)
        if (
            isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.Add)
        )
        or (
            isinstance(node, ast.AugAssign)
            and isinstance(node.op, ast.Add)
        )
    )
    assert sum_additions
    assert all(
        is_inside_fixed_decimal_context(node, parents)
        for node in sum_additions
    )


def test_module_scope_has_no_io_network_storage_execution_or_float_surface() -> None:
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    assert_ast_has_no_forbidden_io(source_text)

    public_names = {
        "ResearchTeamDomainRotationCapacityConfig",
        "ResearchTeamDomainRotationCapacityObservation",
        "ResearchTeamDomainRotationCapacityReasonCodeCount",
        "ResearchTeamDomainRotationCapacityReport",
        "ResearchTeamDomainRotationCapacityRow",
        "build_research_team_domain_rotation_capacity_report",
        "research_team_domain_rotation_capacity_report_payload",
    }
    forbidden_surface_terms = {
        "auth",
        "wallet",
        "order",
        "execution",
        "recommendation",
        "sizing",
        "network",
        "database",
        "persistence",
        "trade",
    }
    assert not any(
        term in name.lower()
        for term in forbidden_surface_terms
        for name in public_names
    )


@pytest.mark.parametrize(
    "source_text",
    (
        "import os as harmless",
        "from subprocess import run as harmless",
        "import socket as harmless",
        "import http.client as harmless",
        "from pathlib import Path as Harmless",
        "__import__('os')",
        "import importlib as loader\nloader.import_module('subprocess')",
        "from importlib import import_module as loader\nloader('socket')",
        "loader = __import__\nloader('http.client')",
        "import importlib as loader\nload = loader.import_module\nload('pathlib')",
    ),
)
def test_ast_no_io_guard_rejects_dynamic_imports_aliases_and_modules(
    source_text: str,
) -> None:
    with pytest.raises(AssertionError):
        assert_ast_has_no_forbidden_io(source_text)
