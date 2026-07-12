from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, fields, replace
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.source_cross_channel_corrob_ranking_report as api
from polymarket_alpha_lab.source_cross_channel_corrob_ranking_report import (
    SourceCrossChannelCorrobRankingReport,
    build_source_cross_channel_corrob_ranking_report,
    source_cross_channel_corrob_ranking_report_payload,
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def test_builds_ranked_pass_report_when_official_independent_matching_and_fresh() -> None:
    report = build_source_cross_channel_corrob_ranking_report(
        official_channel_count=d("2.000000"),
        independent_channel_count=d("3.000000"),
        matching_channel_count=d("5.000000"),
        conflicting_channel_count=d("0.000000"),
        fresh_channel_count=d("5.000000"),
    )

    assert report == SourceCrossChannelCorrobRankingReport(
        official_channel_count=d("2.000000"),
        independent_channel_count=d("3.000000"),
        matching_channel_count=d("5.000000"),
        conflicting_channel_count=d("0.000000"),
        fresh_channel_count=d("5.000000"),
        corroboration_status="pass",
        corroboration_score_probability=d("1.000000"),
        reason_codes=("cross_channel_corroboration_pass",),
        manual_next_step="document_cross_channel_source_ranking",
        payload_digest=report.payload_digest,
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_conflicts_block_and_missing_channel_mix_or_freshness_watch() -> None:
    conflict_report = build_source_cross_channel_corrob_ranking_report(
        official_channel_count=d("1.000000"),
        independent_channel_count=d("2.000000"),
        matching_channel_count=d("3.000000"),
        conflicting_channel_count=d("1.000000"),
        fresh_channel_count=d("3.000000"),
    )
    assert conflict_report.corroboration_status == "block"
    assert conflict_report.reason_codes == ("cross_channel_conflict_detected",)
    assert conflict_report.manual_next_step == "manual_cross_channel_conflict_review"
    assert conflict_report.corroboration_score_probability == d("0.750000")

    insufficient_mix_report = build_source_cross_channel_corrob_ranking_report(
        official_channel_count=d("0.000000"),
        independent_channel_count=d("3.000000"),
        matching_channel_count=d("3.000000"),
        conflicting_channel_count=d("0.000000"),
        fresh_channel_count=d("3.000000"),
    )
    assert insufficient_mix_report.corroboration_status == "watch"
    assert insufficient_mix_report.reason_codes == ("official_channel_missing",)
    assert insufficient_mix_report.manual_next_step == "collect_official_channel_source"
    assert insufficient_mix_report.corroboration_score_probability == d("0.666667")

    stale_report = build_source_cross_channel_corrob_ranking_report(
        official_channel_count=d("1.000000"),
        independent_channel_count=d("1.000000"),
        matching_channel_count=d("2.000000"),
        conflicting_channel_count=d("0.000000"),
        fresh_channel_count=d("1.000000"),
    )
    assert stale_report.corroboration_status == "watch"
    assert stale_report.reason_codes == ("fresh_channel_quorum_missing",)
    assert stale_report.manual_next_step == "refresh_cross_channel_source_evidence"
    assert stale_report.corroboration_score_probability == d("0.500000")


def test_payload_is_json_ready_deterministic_and_digest_validates() -> None:
    report = build_source_cross_channel_corrob_ranking_report(
        official_channel_count=d("1"),
        independent_channel_count=d("2"),
        matching_channel_count=d("2"),
        conflicting_channel_count=d("0"),
        fresh_channel_count=d("2"),
    )

    payload = source_cross_channel_corrob_ranking_report_payload(report)

    json.dumps(payload, sort_keys=True)
    assert payload == report.public_payload
    assert payload["official_channel_count"] == "1.000000"
    assert payload["independent_channel_count"] == "2.000000"
    assert payload["matching_channel_count"] == "2.000000"
    assert payload["conflicting_channel_count"] == "0.000000"
    assert payload["fresh_channel_count"] == "2.000000"
    assert payload["corroboration_score_probability"] == "0.666667"
    assert payload["corroboration_status"] == "pass"
    assert payload["reason_codes"] == ("cross_channel_corroboration_pass",)
    assert payload["manual_next_step"] == "document_cross_channel_source_ranking"
    assert payload["payload_digest"] == report.payload_digest
    assert len(report.payload_digest) == 64
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(report)

    with pytest.raises(ValueError, match="payload_digest"):
        replace(report, payload_digest="0" * 64)

    tampered_payload = dict(payload)
    tampered_payload["matching_channel_count"] = "3.000000"
    with pytest.raises(ValueError, match="payload_digest"):
        source_cross_channel_corrob_ranking_report_payload(tampered_payload)


def test_rejects_non_decimal_inconsistent_counts_flags_and_subclassing() -> None:
    with pytest.raises(ValueError, match="official_channel_count"):
        build_source_cross_channel_corrob_ranking_report(
            official_channel_count=1,
            independent_channel_count=d("1.000000"),
            matching_channel_count=d("1.000000"),
            conflicting_channel_count=d("0.000000"),
            fresh_channel_count=d("1.000000"),
        )
    with pytest.raises(ValueError, match="independent_channel_count"):
        build_source_cross_channel_corrob_ranking_report(
            official_channel_count=d("1.000000"),
            independent_channel_count=_DecimalSubclass("1.000000"),
            matching_channel_count=d("1.000000"),
            conflicting_channel_count=d("0.000000"),
            fresh_channel_count=d("1.000000"),
        )
    with pytest.raises(ValueError, match="channel counts"):
        build_source_cross_channel_corrob_ranking_report(
            official_channel_count=d("1.000000"),
            independent_channel_count=d("1.000000"),
            matching_channel_count=d("1.000000"),
            conflicting_channel_count=d("2.000000"),
            fresh_channel_count=d("1.000000"),
        )
    with pytest.raises(ValueError, match="fresh_channel_count"):
        build_source_cross_channel_corrob_ranking_report(
            official_channel_count=d("1.000000"),
            independent_channel_count=d("1.000000"),
            matching_channel_count=d("1.000000"),
            conflicting_channel_count=d("0.000000"),
            fresh_channel_count=d("3.000000"),
        )
    with pytest.raises(ValueError, match="readonly"):
        build_source_cross_channel_corrob_ranking_report(
            official_channel_count=d("1.000000"),
            independent_channel_count=d("1.000000"),
            matching_channel_count=d("1.000000"),
            conflicting_channel_count=d("0.000000"),
            fresh_channel_count=d("1.000000"),
            readonly=False,
        )

    report = build_source_cross_channel_corrob_ranking_report(
        official_channel_count=d("1.000000"),
        independent_channel_count=d("1.000000"),
        matching_channel_count=d("1.000000"),
        conflicting_channel_count=d("0.000000"),
        fresh_channel_count=d("1.000000"),
    )
    with pytest.raises(FrozenInstanceError):
        report.corroboration_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadReport(SourceCrossChannelCorrobRankingReport):
            pass


def test_module_has_no_network_persistence_or_action_surfaces() -> None:
    source = inspect.getsource(api).lower()
    tree = ast.parse(source)

    assert "float(" not in source
    assert "jsonl" not in source

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
                "delete",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )

    unsafe_terms = (
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("key", "s"),
        _join_parts("sign", "ature"),
        _join_parts("execute"),
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(token in lowered for token in unsafe_terms)
    for field in fields(SourceCrossChannelCorrobRankingReport):
        lowered = field.name.lower()
        assert not any(token in lowered for token in unsafe_terms)


def _walk_public_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            values.extend(_walk_public_values(getattr(value, field.name)))
        return tuple(values)
    if isinstance(value, tuple):
        for item in value:
            values.extend(_walk_public_values(item))
        return tuple(values)
    values.append(value)
    return tuple(values)


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    for item in _walk_public_values(value):
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if type(item) is bool or item is None or isinstance(item, str):
            continue
        if type(item) is int or isinstance(item, float):
            raise AssertionError(f"public numeric value is not Decimal: {item!r}")
