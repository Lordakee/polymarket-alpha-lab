from __future__ import annotations

import hashlib
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_event_resolution_evidence_quorum_tail_report"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "pass_quorum_score_floor": d("0.750000"),
        "block_quorum_score_floor": d("0.500000"),
        "pass_independent_family_count": d("2.000000"),
        "watch_independent_family_count": d("1.000000"),
        "watch_opposition_pressure": d("0.250000"),
        "block_opposition_pressure": d("0.500000"),
        "watch_stale_pressure": d("0.250000"),
        "block_stale_pressure": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchEventResolutionEvidenceQuorumTailConfig(**values)


def observation(
    seed: str = "alpha",
    *,
    evidence_count: Decimal = d("4.000000"),
    independent_family_count: Decimal = d("2.000000"),
    affirming_evidence_count: Decimal = d("4.000000"),
    opposing_evidence_count: Decimal = d("0.000000"),
    stale_evidence_count: Decimal = d("0.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchEventResolutionEvidenceQuorumTailObservation(
        event_digest=digest(f"{seed}-event"),
        resolution_digest=digest(f"{seed}-resolution"),
        evidence_packet_digest=digest(f"{seed}-evidence-packet"),
        evidence_count=evidence_count,
        independent_family_count=independent_family_count,
        affirming_evidence_count=affirming_evidence_count,
        opposing_evidence_count=opposing_evidence_count,
        stale_evidence_count=stale_evidence_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_event_resolution_evidence_quorum_tail_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def assert_no_numeric_objects(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_numeric_objects(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_numeric_objects(item)
        return
    assert type(value) not in (Decimal, float, int)


def unsafe_terms() -> tuple[str, ...]:
    return (
        _join_parts("cand", "idate"),
        _join_parts("mark", "et"),
        _join_parts("sl", "ug"),
        _join_parts("que", "stion"),
        _join_parts("sour", "ce"),
        _join_parts("ur", "l"),
        _join_parts("te", "xt"),
        _join_parts("d", "sn"),
        _join_parts("ta", "ble"),
        _join_parts("to", "ken"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        _join_parts("li", "ve"),
        _join_parts("siz", "ing"),
        _join_parts("recomm", "endation"),
    )


def test_empty_report_is_pass_readonly_digest_validated_and_decimal_only() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchEventResolutionEvidenceQuorumTailReport
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen
    assert report.generated_at == GENERATED_AT
    assert report.status == "pass"
    assert report.event_count == d("0.000000")
    assert report.pass_event_count == d("0.000000")
    assert report.watch_event_count == d("0.000000")
    assert report.block_event_count == d("0.000000")
    assert report.quorum_tail_event_count == d("0.000000")
    assert report.maximum_tail_risk_score == d("0.000000")
    assert report.average_quorum_score == d("0.000000")
    assert report.average_tail_risk_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "research_event_resolution_evidence_quorum_tail_empty",
    )
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)
    assert (
        report.derived_validation_digest
        == module.research_event_resolution_evidence_quorum_tail_report_digest(report)
    )
    assert module.validate_research_event_resolution_evidence_quorum_tail_report_digest(
        report,
    )
    payload = report.payload
    assert payload == module.research_event_resolution_evidence_quorum_tail_report_payload(
        report,
    )
    assert payload["event_count"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_numeric_objects(payload)
    json.dumps(payload, sort_keys=True)


def test_tail_rows_classify_pass_watch_and_block_deterministically() -> None:
    pass_item = observation("pass")
    watch_item = observation(
        "watch",
        affirming_evidence_count=d("2.000000"),
    )
    block_item = observation(
        "block",
        independent_family_count=d("0.000000"),
        affirming_evidence_count=d("1.000000"),
        opposing_evidence_count=d("2.000000"),
        stale_evidence_count=d("2.000000"),
    )

    forward = build_report(pass_item, watch_item, block_item)
    reverse = build_report(block_item, watch_item, pass_item)

    assert forward == reverse
    assert forward.status == "block"
    assert forward.event_count == d("3.000000")
    assert forward.pass_event_count == d("1.000000")
    assert forward.watch_event_count == d("1.000000")
    assert forward.block_event_count == d("1.000000")
    assert forward.quorum_tail_event_count == d("2.000000")
    assert forward.maximum_tail_risk_score == d("1.000000")
    assert forward.average_quorum_score == d("0.583333")
    assert forward.average_tail_risk_score == d("0.500000")
    assert forward.reason_codes == (
        "evidence_quorum_tail_block",
        "evidence_quorum_tail_watch",
        "evidence_quorum_tail_pass",
    )

    assert tuple(row.event_digest for row in forward.rows) == (
        digest("block-event"),
        digest("watch-event"),
        digest("pass-event"),
    )
    blocked, watched, passed = forward.rows
    assert blocked.rank == d("1.000000")
    assert blocked.status == "block"
    assert blocked.quorum_score == d("0.250000")
    assert blocked.independence_score == d("0.000000")
    assert blocked.opposition_pressure == d("0.500000")
    assert blocked.stale_pressure == d("0.500000")
    assert blocked.tail_risk_score == d("1.000000")
    assert blocked.reason_codes == (
        "evidence_quorum_tail_block",
        "low_quorum_score_block",
        "insufficient_independent_family_block",
        "opposition_pressure_block",
        "stale_evidence_pressure_block",
    )
    assert watched.rank == d("2.000000")
    assert watched.status == "watch"
    assert watched.quorum_score == d("0.500000")
    assert watched.tail_risk_score == d("0.500000")
    assert watched.reason_codes == (
        "evidence_quorum_tail_watch",
        "low_quorum_score_watch",
    )
    assert passed.rank == d("3.000000")
    assert passed.status == "pass"
    assert passed.tail_risk_score == d("0.000000")
    assert passed.reason_codes == ("evidence_quorum_tail_pass",)


def test_payload_serialization_and_validation_reject_tampering() -> None:
    module = api()
    report = build_report(observation("zeta"), observation("alpha"))
    repeated = build_report(observation("alpha"), observation("zeta"))
    payload = module.research_event_resolution_evidence_quorum_tail_report_payload(
        report,
    )

    assert report == repeated
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["event_count"] == "2.000000"
    assert payload["rows"][0]["tail_risk_score"] == "0.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert module.validate_research_event_resolution_evidence_quorum_tail_report_payload(
        payload,
    )
    assert_no_numeric_objects(payload)
    encoded = json.dumps(payload, sort_keys=True)
    assert encoded == json.dumps(repeated.payload, sort_keys=True)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    tampered_payload = dict(payload)
    tampered_payload["event_count"] = "99.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_event_resolution_evidence_quorum_tail_report_payload(
            tampered_payload,
        )

    invalid_status_payload = dict(payload)
    invalid_status_payload["status"] = "ready"
    invalid_status_payload["derived_validation_digest"] = hashlib.sha256(
        json.dumps(
            {
                key: value
                for key, value in invalid_status_payload.items()
                if key != "derived_validation_digest"
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()
    with pytest.raises(ValueError, match="status"):
        module.validate_research_event_resolution_evidence_quorum_tail_report_payload(
            invalid_status_payload,
        )

    numeric_payload = dict(payload)
    numeric_payload["event_count"] = 1
    with pytest.raises(ValueError, match="public payload"):
        module.validate_research_event_resolution_evidence_quorum_tail_report_payload(
            numeric_payload,
        )

    flag_payload = dict(payload)
    flag_payload["readonly"] = False
    with pytest.raises(ValueError, match="payload readonly must be True"):
        module.validate_research_event_resolution_evidence_quorum_tail_report_payload(
            flag_payload,
        )

    unsafe_payload = dict(payload)
    unsafe_payload[_join_parts("mark", "et_slug")] = "redacted"
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_research_event_resolution_evidence_quorum_tail_report_payload(
            unsafe_payload,
        )


def test_public_dataclasses_are_frozen_decimal_only_and_reject_subclassing() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_RESEARCH_EVENT_RESOLUTION_EVIDENCE_QUORUM_TAIL_REPORT_CONFIG_VERSION",
        "ResearchEventResolutionEvidenceQuorumTailConfig",
        "ResearchEventResolutionEvidenceQuorumTailObservation",
        "ResearchEventResolutionEvidenceQuorumTailRow",
        "ResearchEventResolutionEvidenceQuorumTailReport",
        "build_research_event_resolution_evidence_quorum_tail_report",
        "research_event_resolution_evidence_quorum_tail_report_digest",
        "research_event_resolution_evidence_quorum_tail_report_payload",
        "validate_research_event_resolution_evidence_quorum_tail_report_digest",
        "validate_research_event_resolution_evidence_quorum_tail_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen

    report = build_report(observation())
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(module.ResearchEventResolutionEvidenceQuorumTailConfig):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeObservation(
            module.ResearchEventResolutionEvidenceQuorumTailObservation,
        ):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeRow(module.ResearchEventResolutionEvidenceQuorumTailRow):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(module.ResearchEventResolutionEvidenceQuorumTailReport):
            pass

    with pytest.raises(ValueError, match="evidence_count"):
        observation(evidence_count=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="ready")

    for item in (config(), *report.rows, report):
        for field in fields(item):
            value = getattr(item, field.name)
            assert type(value) is not float
            if field.name.endswith(("_count", "_score", "_rank", "_pressure")):
                assert type(value) is Decimal


def test_validation_rejects_bad_types_thresholds_counts_and_duplicates() -> None:
    module = api()
    with pytest.raises(ValueError, match="block_quorum_score_floor"):
        config(block_quorum_score_floor=d("0.750000"))
    with pytest.raises(ValueError, match="watch_independent_family_count"):
        config(watch_independent_family_count=d("3.000000"))
    with pytest.raises(ValueError, match="pass_quorum_score_floor"):
        config(pass_quorum_score_floor=0.75)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="event_digest"):
        module.ResearchEventResolutionEvidenceQuorumTailObservation(
            event_digest="not-a-digest",
            resolution_digest=digest("resolution"),
            evidence_packet_digest=digest("evidence"),
            evidence_count=d("1.000000"),
            independent_family_count=d("1.000000"),
            affirming_evidence_count=d("1.000000"),
            opposing_evidence_count=d("0.000000"),
            stale_evidence_count=d("0.000000"),
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_event_resolution_evidence_quorum_tail_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 9, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_event_resolution_evidence_quorum_tail_report(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="affirming_evidence_count"):
        observation(affirming_evidence_count=d("5.000000"))
    with pytest.raises(ValueError, match="opposing_evidence_count"):
        observation(opposing_evidence_count=d("5.000000"))
    with pytest.raises(ValueError, match="stale_evidence_count"):
        observation(stale_evidence_count=d("5.000000"))
    with pytest.raises(ValueError, match="duplicate digests"):
        build_report(observation("dupe"), observation("dupe"))


def test_module_has_no_execution_or_unsafe_public_surfaces() -> None:
    module = api()
    public_names = set(module.__all__) | {
        name for name in dir(module) if not name.startswith("_")
    }
    for public_name in public_names:
        lower_name = public_name.lower()
        assert "db" not in lower_name
        for term in unsafe_terms():
            assert term not in lower_name

    payload = build_report(observation("safe")).payload
    encoded = json.dumps(payload, sort_keys=True).lower()
    for term in unsafe_terms():
        assert term not in encoded
    for leaked in (
        "raw-candidate-id",
        "market-alpha",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "postgres://",
        "wallet surface",
        "place order",
        "trade execution",
    ):
        assert leaked not in encoded

    source = inspect.getsource(module)
    for forbidden in (
        "requests",
        "urllib",
        "http.client",
        "socket",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "subprocess",
        "Path(",
        "open(",
        ".write(",
        ".read(",
        _join_parts("cand", "idate"),
        _join_parts("mark", "et"),
        _join_parts("sl", "ug"),
        _join_parts("que", "stion"),
        _join_parts("sour", "ce"),
        _join_parts("ur", "l"),
        _join_parts("te", "xt"),
        _join_parts("d", "sn"),
        _join_parts("ta", "ble"),
        _join_parts("to", "ken"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        _join_parts("li", "ve"),
        _join_parts("siz", "ing"),
        _join_parts("recomm", "endation"),
    ):
        assert forbidden not in source
