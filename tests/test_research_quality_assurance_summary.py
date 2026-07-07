from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _api() -> Any:
    return import_module("polymarket_alpha_lab.research_quality_assurance_summary")


def _config(**overrides: object) -> Any:
    api = _api()
    values = {
        "min_pass_component_score": d("0.750000"),
        "min_watch_component_score": d("0.500000"),
    }
    values.update(overrides)
    return api.ResearchQualityAssuranceSummaryConfig(**values)


def _component(
    component: str,
    *,
    status: str = "pass",
    quality_score: Decimal = d("0.900000"),
    checked_item_count: Decimal = d("3.000000"),
    issue_count: Decimal = d("0.000000"),
    reason_codes: tuple[str, ...] = (),
    public_summary: str | None = None,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    api = _api()
    return api.ResearchQualityAssuranceComponentSignal(
        component=component,
        status=status,
        quality_score=quality_score,
        checked_item_count=checked_item_count,
        issue_count=issue_count,
        reason_codes=reason_codes,
        public_summary=public_summary,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _complete_components(**overrides: Any) -> tuple[Any, ...]:
    values = {
        "evidence_packet": _component("evidence_packet"),
        "source_quality_matrix": _component("source_quality_matrix"),
        "parsing_quality_matrix": _component("parsing_quality_matrix"),
        "manual_review_checklist": _component("manual_review_checklist"),
    }
    values.update(overrides)
    return tuple(values.values())


def _report(components: tuple[Any, ...] | list[Any]) -> Any:
    api = _api()
    return api.build_research_quality_assurance_summary(
        components,
        config=_config(),
    )


def _walk_strings(value: object) -> tuple[str, ...]:
    if isinstance(value, dict):
        strings: list[str] = []
        for key, nested in value.items():
            strings.append(key)
            strings.extend(_walk_strings(nested))
        return tuple(strings)
    if isinstance(value, list):
        strings = []
        for nested in value:
            strings.extend(_walk_strings(nested))
        return tuple(strings)
    if type(value) is str:
        return (value,)
    return ()


def _assert_json_ready(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            assert type(key) is str
            _assert_json_ready(nested)
        return
    if isinstance(value, list):
        for nested in value:
            _assert_json_ready(nested)
        return
    assert value is None or type(value) in (str, bool)


def _assert_no_public_numeric_scalars(value: object) -> None:
    if type(value) in (Decimal, int, float):
        pytest.fail(f"public payload numeric value was not serialized: {value!r}")
    if isinstance(value, dict):
        for nested in value.values():
            _assert_no_public_numeric_scalars(nested)
    if isinstance(value, list):
        for nested in value:
            _assert_no_public_numeric_scalars(nested)


def test_quality_assurance_summary_passes_when_all_research_checks_pass() -> None:
    report = _report(
        _complete_components(
            evidence_packet=_component(
                "evidence_packet",
                quality_score=d("0.880000"),
                checked_item_count=d("4.000000"),
            ),
            source_quality_matrix=_component(
                "source_quality_matrix",
                quality_score=d("0.910000"),
            ),
            parsing_quality_matrix=_component(
                "parsing_quality_matrix",
                quality_score=d("0.870000"),
            ),
            manual_review_checklist=_component(
                "manual_review_checklist",
                quality_score=d("0.930000"),
            ),
        ),
    )

    assert report.status == "pass"
    assert report.required_component_count == d("4.000000")
    assert report.observed_component_count == d("4.000000")
    assert report.missing_component_count == d("0.000000")
    assert report.pass_count == d("4.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.minimum_component_quality_score == d("0.870000")
    assert report.average_component_quality_score == d("0.897500")
    assert report.reason_codes == ("research_quality_assurance_pass",)
    assert tuple(row.component for row in report.rows) == (
        "evidence_packet",
        "source_quality_matrix",
        "parsing_quality_matrix",
        "manual_review_checklist",
    )
    assert tuple(row.component_key for row in report.rows) == (
        "redacted-research-check-001",
        "redacted-research-check-002",
        "redacted-research-check-003",
        "redacted-research-check-004",
    )
    assert all(row.status == "pass" for row in report.rows)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_quality_assurance_summary_watches_nonblocking_research_quality_gaps() -> None:
    report = _report(
        _complete_components(
            source_quality_matrix=_component(
                "source_quality_matrix",
                status="watch",
                quality_score=d("0.800000"),
                issue_count=d("1.000000"),
                reason_codes=("cross_check_needed",),
            ),
        ),
    )

    assert report.status == "watch"
    assert report.pass_count == d("3.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("0.000000")
    assert report.reason_codes == (
        "component_issue_watch",
        "input_status_watch",
        "input_cross_check_needed",
        "research_quality_assurance_watch",
    )
    row = report.rows[1]
    assert row.component == "source_quality_matrix"
    assert row.status == "watch"
    assert row.reason_codes == (
        "component_issue_watch",
        "input_status_watch",
        "input_cross_check_needed",
    )


def test_quality_assurance_summary_blocks_missing_or_blocking_components() -> None:
    missing_report = _report(
        (
            _component("evidence_packet"),
            _component("source_quality_matrix"),
            _component("manual_review_checklist"),
        ),
    )

    assert missing_report.status == "block"
    assert missing_report.observed_component_count == d("3.000000")
    assert missing_report.missing_component_count == d("1.000000")
    assert missing_report.block_count == d("0.000000")
    assert missing_report.reason_codes == (
        "missing_required_component",
        "research_quality_assurance_block",
    )

    blocking_report = _report(
        _complete_components(
            parsing_quality_matrix=_component(
                "parsing_quality_matrix",
                status="block",
                quality_score=d("0.420000"),
                issue_count=d("2.000000"),
            ),
        ),
    )

    assert blocking_report.status == "block"
    assert blocking_report.missing_component_count == d("0.000000")
    assert blocking_report.block_count == d("1.000000")
    assert blocking_report.rows[2].status == "block"
    assert blocking_report.rows[2].reason_codes == (
        "component_issue_block",
        "input_status_block",
        "low_component_quality_block",
    )


def test_quality_assurance_summary_rejects_types_subclasses_and_mutation() -> None:
    api = _api()

    with pytest.raises(ValueError, match="Decimal"):
        _config(min_pass_component_score=1)
    with pytest.raises(ValueError, match="Decimal"):
        _config(min_pass_component_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="Decimal"):
        _component("evidence_packet", quality_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="components must be a list or tuple"):
        api.build_research_quality_assurance_summary(
            (_component("evidence_packet") for _ in range(1)),
            config=_config(),
        )
    with pytest.raises(ValueError, match="components must contain"):
        api.build_research_quality_assurance_summary([object()], config=_config())

    report = _report(_complete_components())
    with pytest.raises(FrozenInstanceError):
        report.status = "block"  # type: ignore[misc]
    with pytest.raises(TypeError):

        class InvalidSignal(api.ResearchQualityAssuranceComponentSignal):
            pass


def test_quality_assurance_summary_rejects_leaks_in_inputs_and_payload() -> None:
    api = _api()

    with pytest.raises(ValueError, match="unsafe"):
        _component("evidence_packet", public_summary="raw candidate id rc-42")
    with pytest.raises(ValueError, match="unsafe"):
        _component("evidence_packet", reason_codes=("source_url_present",))
    with pytest.raises(ValueError, match="unsafe"):
        _component("evidence_packet", public_summary="https://example.test/source")
    with pytest.raises(ValueError, match="unsafe"):
        _component("evidence_packet", public_summary="manual recommendation to buy")

    payload = api.research_quality_assurance_summary_payload(_report(_complete_components()))

    bad_key_payload = dict(payload)
    bad_key_payload["market_slug"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        api.research_quality_assurance_summary_payload(bad_key_payload)

    bad_value_payload = dict(payload)
    bad_value_payload["reason_codes"] = ["wallet_auth_required"]
    with pytest.raises(ValueError, match="unsafe"):
        api.research_quality_assurance_summary_payload(bad_value_payload)

    bad_nested_payload = dict(payload)
    bad_nested_payload["rows"] = [dict(payload["rows"][0], public_summary="source text leak")]
    with pytest.raises(ValueError, match="unsafe"):
        api.research_quality_assurance_summary_payload(bad_nested_payload)


def test_quality_assurance_summary_enforces_hard_report_only_flags() -> None:
    api = _api()

    with pytest.raises(ValueError, match="report_only"):
        _config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        _component("evidence_packet", readonly=False)

    payload = api.research_quality_assurance_summary_payload(_report(_complete_components()))
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["paper_only"] is True
    assert payload["rows"][0]["report_only"] is True
    assert payload["rows"][0]["readonly"] is True

    bad_flag_payload = dict(payload)
    bad_flag_payload["report_only"] = False
    with pytest.raises(ValueError, match="report_only"):
        api.research_quality_assurance_summary_payload(bad_flag_payload)


def test_quality_assurance_summary_payload_is_deterministic_and_public() -> None:
    api = _api()
    components = _complete_components(
        evidence_packet=_component(
            "evidence_packet",
            quality_score=d("0.800000"),
            checked_item_count=d("5.000000"),
        ),
        manual_review_checklist=_component(
            "manual_review_checklist",
            quality_score=d("0.760000"),
        ),
    )

    forward_payload = api.research_quality_assurance_summary_payload(_report(components))
    reverse_payload = api.research_quality_assurance_summary_payload(
        _report(tuple(reversed(components))),
    )

    assert forward_payload == reverse_payload
    assert len(forward_payload["derived_validation_digest"]) == 64
    _assert_json_ready(forward_payload)
    _assert_no_public_numeric_scalars(forward_payload)
    json.dumps(forward_payload, sort_keys=True)

    forbidden_fragments = (
        "raw-candidate-42",
        "raw candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "https://",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
    )
    public_surface = "\n".join(_walk_strings(forward_payload)).lower()
    for fragment in forbidden_fragments:
        assert fragment not in public_surface

    module_path = (
        Path(__file__).parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_quality_assurance_summary.py"
    )
    module_text = module_path.read_text(encoding="utf-8")
    forbidden_imports = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "sqlite",
        "psycopg",
        "supabase",
        "sqlalchemy",
    )
    for forbidden in forbidden_imports:
        assert forbidden not in module_text
