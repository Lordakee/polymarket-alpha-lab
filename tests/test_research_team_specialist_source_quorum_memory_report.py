from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
import importlib
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_specialist_source_quorum_memory_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_specialist_source_quorum_memory_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "min_pass_independent_family_count": d("3.000000"),
        "min_watch_independent_family_count": d("2.000000"),
        "min_pass_quorum_ratio": d("0.800000"),
        "min_watch_quorum_ratio": d("0.600000"),
        "min_pass_memory_coverage_ratio": d("0.750000"),
        "min_watch_memory_coverage_ratio": d("0.500000"),
        "max_pass_stale_memory_ratio": d("0.100000"),
        "max_watch_stale_memory_ratio": d("0.250000"),
    }
    values.update(overrides)
    return module.ResearchTeamSpecialistSourceQuorumMemoryConfig(**values)


def observation(
    team_label: str = "team.alpha",
    specialist_label: str = "specialist.macro",
    evidence_family_label: str = "family.primary",
    *,
    observed_at: datetime = GENERATED_AT - timedelta(minutes=20),
    independent_family_count: Decimal = d("5.000000"),
    quorum_confirmed_family_count: Decimal = d("5.000000"),
    memory_check_count: Decimal = d("10.000000"),
    memory_confirmed_count: Decimal = d("8.000000"),
    stale_memory_count: Decimal = d("1.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchTeamSpecialistSourceQuorumMemoryObservation(
        team_label=team_label,
        specialist_label=specialist_label,
        evidence_family_label=evidence_family_label,
        observed_at=observed_at,
        independent_family_count=independent_family_count,
        quorum_confirmed_family_count=quorum_confirmed_family_count,
        memory_check_count=memory_check_count,
        memory_confirmed_count=memory_confirmed_count,
        stale_memory_count=stale_memory_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
):
    module = api()
    return module.build_research_team_specialist_source_quorum_memory_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def assert_no_raw_numeric_payload_values(value: object) -> None:
    if type(value) is bool or value is None or type(value) is str:
        return
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"public numeric value must be a string, got {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_raw_numeric_payload_values(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_raw_numeric_payload_values(item)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
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


def assert_no_forbidden_public_payload_surface(value: object) -> None:
    blocked_parts = (
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "trading",
        "live",
        "sizing",
        "recommend",
        "http://",
        "https://",
        "://",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            assert not any(part in lowered_key for part in blocked_parts)
            assert_no_forbidden_public_payload_surface(item)
        return
    if isinstance(value, str):
        lowered_value = value.lower()
        assert not any(part in lowered_value for part in blocked_parts)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_forbidden_public_payload_surface(item)


def test_empty_observations_block_as_readonly_report_only_gap() -> None:
    module = api()

    quorum_memory = report()

    assert type(quorum_memory) is module.ResearchTeamSpecialistSourceQuorumMemoryReport
    assert module.RESEARCH_TEAM_SPECIALIST_SOURCE_QUORUM_MEMORY_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert quorum_memory.config_version == (
        module.DEFAULT_RESEARCH_TEAM_SPECIALIST_SOURCE_QUORUM_MEMORY_CONFIG_VERSION
    )
    assert quorum_memory.status == "block"
    assert quorum_memory.next_review_step == "block_quorum_memory_until_review"
    assert quorum_memory.observation_count == d("0.000000")
    assert quorum_memory.team_count == d("0.000000")
    assert quorum_memory.specialist_count == d("0.000000")
    assert quorum_memory.evidence_family_count == d("0.000000")
    assert quorum_memory.independent_family_count == d("0.000000")
    assert quorum_memory.quorum_confirmed_family_count == d("0.000000")
    assert quorum_memory.memory_check_count == d("0.000000")
    assert quorum_memory.memory_confirmed_count == d("0.000000")
    assert quorum_memory.stale_memory_count == d("0.000000")
    assert quorum_memory.pass_count == d("0.000000")
    assert quorum_memory.watch_count == d("0.000000")
    assert quorum_memory.block_count == d("0.000000")
    assert quorum_memory.quorum_ratio == d("0.000000")
    assert quorum_memory.memory_coverage_ratio == d("0.000000")
    assert quorum_memory.stale_memory_ratio == d("0.000000")
    assert quorum_memory.quorum_memory_score == d("0.000000")
    assert quorum_memory.rows == ()
    assert quorum_memory.reason_codes == ("source_quorum_memory_no_observations",)
    assert quorum_memory.reason_code_counts == (
        module.ResearchTeamSpecialistSourceQuorumMemoryReasonCodeCount(
            reason_code="source_quorum_memory_no_observations",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert quorum_memory.paper_only is True
    assert quorum_memory.report_only is True
    assert quorum_memory.readonly is True
    assert len(quorum_memory.derived_validation_digest) == 64


def test_report_aggregates_statuses_and_quorum_memory_scores() -> None:
    quorum_memory = report(
        observation(
            "team.gamma",
            "specialist.blocked",
            "family.tertiary",
            independent_family_count=d("1.000000"),
            quorum_confirmed_family_count=d("1.000000"),
            memory_confirmed_count=d("4.000000"),
            stale_memory_count=d("4.000000"),
        ),
        observation(
            "team.beta",
            "specialist.watch",
            "family.secondary",
            independent_family_count=d("2.000000"),
            quorum_confirmed_family_count=d("2.000000"),
            memory_confirmed_count=d("6.000000"),
            stale_memory_count=d("2.000000"),
        ),
        observation("team.alpha", "specialist.pass", "family.primary"),
    )

    assert quorum_memory.status == "block"
    assert quorum_memory.next_review_step == "block_quorum_memory_until_review"
    assert quorum_memory.observation_count == d("3.000000")
    assert quorum_memory.team_count == d("3.000000")
    assert quorum_memory.specialist_count == d("3.000000")
    assert quorum_memory.evidence_family_count == d("3.000000")
    assert quorum_memory.independent_family_count == d("8.000000")
    assert quorum_memory.quorum_confirmed_family_count == d("8.000000")
    assert quorum_memory.memory_check_count == d("30.000000")
    assert quorum_memory.memory_confirmed_count == d("18.000000")
    assert quorum_memory.stale_memory_count == d("7.000000")
    assert quorum_memory.pass_count == d("1.000000")
    assert quorum_memory.watch_count == d("1.000000")
    assert quorum_memory.block_count == d("1.000000")
    assert quorum_memory.quorum_ratio == d("1.000000")
    assert quorum_memory.memory_coverage_ratio == d("0.600000")
    assert quorum_memory.stale_memory_ratio == d("0.233333")
    assert quorum_memory.quorum_memory_score == d("0.788889")
    assert quorum_memory.reason_codes == (
        "source_quorum_memory_block_present",
        "source_quorum_memory_watch_present",
        "memory_coverage_gap_present",
        "stale_memory_gap_present",
    )

    assert tuple(
        (row.team_label, row.specialist_label, row.evidence_family_label, row.status)
        for row in quorum_memory.rows
    ) == (
        ("team.gamma", "specialist.blocked", "family.tertiary", "block"),
        ("team.beta", "specialist.watch", "family.secondary", "watch"),
        ("team.alpha", "specialist.pass", "family.primary", "pass"),
    )
    blocked, watched, passed = quorum_memory.rows
    assert blocked.quorum_ratio == d("1.000000")
    assert blocked.memory_coverage_ratio == d("0.400000")
    assert blocked.stale_memory_ratio == d("0.400000")
    assert blocked.quorum_memory_score == d("0.666667")
    assert blocked.reason_codes == (
        "source_quorum_block",
        "memory_coverage_block",
        "stale_memory_block",
    )
    assert watched.quorum_memory_score == d("0.800000")
    assert watched.reason_codes == (
        "source_quorum_watch",
        "memory_coverage_watch",
        "stale_memory_watch",
    )
    assert passed.quorum_memory_score == d("0.900000")
    assert passed.reason_codes == ("source_quorum_memory_clear",)
    assert quorum_memory.reason_code_counts[0].reason_code == "source_quorum_block"
    assert quorum_memory.reason_code_counts[0].count == d("1.000000")
    assert quorum_memory.reason_code_counts[0].row_ratio == d("0.333333")


def test_payload_is_deterministic_digest_bound_decimal_string_only_and_public_safe() -> None:
    module = api()
    first = report(
        observation("team.beta", "specialist.watch", "family.secondary"),
        observation("team.alpha", "specialist.pass", "family.primary"),
    )
    second = report(
        observation("team.alpha", "specialist.pass", "family.primary"),
        observation("team.beta", "specialist.watch", "family.secondary"),
    )

    first_payload = module.research_team_specialist_source_quorum_memory_report_payload(first)
    second_payload = module.research_team_specialist_source_quorum_memory_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first == second
    assert first_payload == second_payload
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert module.research_team_specialist_source_quorum_memory_report_digest(first) == (
        first.derived_validation_digest
    )
    assert first_payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert first_payload["observation_count"] == "2.000000"
    assert first_payload["rows"][0]["team_label"] == "team.alpha"
    assert first_payload["rows"][0]["quorum_memory_score"] == "0.900000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert '"0.900000"' in encoded
    assert_no_raw_numeric_payload_values(first_payload)
    assert_no_forbidden_public_payload_surface(first_payload)

    tampered = dict(first_payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_specialist_source_quorum_memory_report_payload(tampered)

    unsafe_key = dict(first_payload)
    unsafe_key["wallet_address"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_team_specialist_source_quorum_memory_report_payload(unsafe_key)

    unsafe_value = dict(first_payload)
    unsafe_value["rows"] = [
        {**first_payload["rows"][0], "team_label": "market_id_linked"},
        *first_payload["rows"][1:],
    ]
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_team_specialist_source_quorum_memory_report_payload(unsafe_value)


def test_validation_freezing_flags_decimal_only_statuses_and_consistency() -> None:
    module = api()
    quorum_memory = report(observation())

    assert quorum_memory.generated_at == GENERATED_AT
    assert quorum_memory.rows[0].observed_at == GENERATED_AT - timedelta(minutes=20)
    assert quorum_memory.status in {"pass", "watch", "block"}
    assert all(row.status in {"pass", "watch", "block"} for row in quorum_memory.rows)

    for public_type in (
        module.ResearchTeamSpecialistSourceQuorumMemoryConfig,
        module.ResearchTeamSpecialistSourceQuorumMemoryObservation,
        module.ResearchTeamSpecialistSourceQuorumMemoryRow,
        module.ResearchTeamSpecialistSourceQuorumMemoryReasonCodeCount,
        module.ResearchTeamSpecialistSourceQuorumMemoryReport,
    ):
        assert is_dataclass(public_type)

    for item in (
        config(),
        observation(),
        quorum_memory.rows[0],
        quorum_memory.reason_code_counts[0],
        quorum_memory,
    ):
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_public_numeric_values_are_decimal(item)

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        observation(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        report(observation(readonly=False))

    values = {field.name: getattr(quorum_memory, field.name) for field in fields(quorum_memory)}
    values["derived_validation_digest"] = "f" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.ResearchTeamSpecialistSourceQuorumMemoryReport(**values)


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        ("independent_family_count", Decimal("0.000000"), "independent_family_count"),
        ("quorum_confirmed_family_count", d("-1.000000"), "quorum_confirmed_family_count"),
        ("memory_check_count", d("0.000000"), "memory_check_count"),
        ("memory_confirmed_count", d("11.000000"), "memory_confirmed_count"),
        ("stale_memory_count", d("11.000000"), "stale_memory_count"),
        ("memory_confirmed_count", 8, "memory_confirmed_count must be exactly Decimal"),
        (
            "stale_memory_count",
            _DecimalSubclass("1.000000"),
            "stale_memory_count must be exactly Decimal",
        ),
        ("independent_family_count", d("1.500000"), "independent_family_count"),
        ("quorum_confirmed_family_count", Decimal("NaN"), "quorum_confirmed_family_count"),
    ),
)
def test_validation_rejects_invalid_decimal_inputs(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        observation(**{field_name: bad_value})


def test_validation_rejects_unsafe_labels_datetimes_thresholds_and_wrong_types() -> None:
    module = api()

    with pytest.raises(ValueError, match="team_label"):
        observation(team_label=" ")
    with pytest.raises(ValueError, match="specialist_label"):
        observation(specialist_label="candidate_id:123")
    with pytest.raises(ValueError, match="evidence_family_label"):
        observation(evidence_family_label="https://example.invalid/source")
    with pytest.raises(ValueError, match="observed_at must be exactly datetime"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 9, tzinfo=UTC))
    with pytest.raises(ValueError, match="min_watch_quorum_ratio"):
        config(min_watch_quorum_ratio=d("0.900000"))
    with pytest.raises(ValueError, match="max_pass_stale_memory_ratio"):
        config(max_pass_stale_memory_ratio=d("0.300000"))
    with pytest.raises(ValueError, match="config"):
        report(observation(), cfg=object())
    with pytest.raises(ValueError, match="observations"):
        module.build_research_team_specialist_source_quorum_memory_report(object())


def test_module_scope_has_no_file_database_network_or_execution_surfaces() -> None:
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
        "rollback",
        "send",
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
