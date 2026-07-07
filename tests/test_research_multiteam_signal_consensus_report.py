from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 7, 11, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _MissingOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_multiteam_signal_consensus_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object):
    module = api()
    values = {
        "min_team_count": d("3"),
        "pass_min_consensus_ratio": d("0.700000"),
        "review_conflict_strength": d("0.250000"),
        "block_conflict_strength": d("0.600000"),
        "min_average_confidence_score": d("0.600000"),
    }
    values.update(overrides)
    return module.ResearchMultiteamSignalConsensusConfig(**values)


def _signal(
    team_id: str,
    *,
    category_id: str,
    signal_direction: str,
    signal_strength: Decimal,
    confidence_score: Decimal,
    observed_at: datetime = OBSERVED_AT,
    review_required: bool = False,
):
    module = api()
    return module.ResearchMultiteamSignal(
        team_id=team_id,
        category_id=category_id,
        observed_at=observed_at,
        signal_direction=signal_direction,
        signal_strength=signal_strength,
        confidence_score=confidence_score,
        review_required=review_required,
    )


def _build_report(*signals, config=None):
    module = api()
    return module.build_research_multiteam_signal_consensus_report(
        signals,
        config=_config() if config is None else config,
        generated_at=GENERATED_AT,
    )


def test_block_report_scores_conflict_strength_review_need_and_sorts_rows() -> None:
    report = _build_report(
        _signal(
            "sports_other",
            category_id="sports.other",
            signal_direction="supports_no",
            signal_strength=d("0.900000"),
            confidence_score=d("0.900000"),
            review_required=True,
        ),
        _signal(
            "politics",
            category_id="politics",
            signal_direction="supports_yes",
            signal_strength=d("0.900000"),
            confidence_score=d("0.800000"),
        ),
        _signal(
            "crypto_btc",
            category_id="finance.crypto.btc",
            signal_direction="supports_yes",
            signal_strength=d("0.700000"),
            confidence_score=d("0.900000"),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.team_count == d("3")
    assert report.category_count == d("3")
    assert report.aligned_team_count == d("2")
    assert report.conflicting_team_count == d("1")
    assert report.review_required_count == d("1")
    assert report.dominant_signal_direction == "supports_yes"
    assert report.consensus_ratio == d("0.625000")
    assert report.conflict_strength == d("0.750000")
    assert report.review_need_score == d("0.750000")
    assert report.average_confidence_score == d("0.866667")
    assert report.reason_codes == (
        "cross_team_conflict_block",
        "team_review_requested",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.team_id for row in report.rows) == (
        "sports_other",
        "crypto_btc",
        "politics",
    )
    conflict_row = report.rows[0]
    assert conflict_row.alignment_status == "conflict"
    assert conflict_row.signal_weight == d("0.810000")
    assert conflict_row.reason_codes == (
        "team_signal_conflict",
        "team_review_requested",
    )
    assert all(type(row.signal_weight) is Decimal for row in report.rows)


def test_pass_and_watch_statuses_are_report_only_and_deterministic() -> None:
    passing = _build_report(
        _signal(
            "politics",
            category_id="politics",
            signal_direction="supports_yes",
            signal_strength=d("0.900000"),
            confidence_score=d("0.900000"),
        ),
        _signal(
            "crypto_btc",
            category_id="finance.crypto.btc",
            signal_direction="supports_yes",
            signal_strength=d("0.800000"),
            confidence_score=d("0.800000"),
        ),
        _signal(
            "sports_other",
            category_id="sports.other",
            signal_direction="supports_yes",
            signal_strength=d("0.700000"),
            confidence_score=d("0.700000"),
        ),
    )

    assert passing.status == "pass"
    assert passing.consensus_ratio == d("1.000000")
    assert passing.conflict_strength == d("0.000000")
    assert passing.review_need_score == d("0.000000")
    assert passing.reason_codes == ("signal_consensus_pass",)

    watch_a = _build_report(
        _signal(
            "sports_other",
            category_id="sports.other",
            signal_direction="neutral",
            signal_strength=d("0.900000"),
            confidence_score=d("0.900000"),
        ),
        _signal(
            "politics",
            category_id="politics",
            signal_direction="supports_yes",
            signal_strength=d("0.700000"),
            confidence_score=d("0.600000"),
        ),
        _signal(
            "crypto_btc",
            category_id="finance.crypto.btc",
            signal_direction="supports_yes",
            signal_strength=d("0.600000"),
            confidence_score=d("0.600000"),
        ),
    )
    watch_b = _build_report(*reversed(watch_a.rows))

    assert watch_a == watch_b
    assert watch_a.status == "watch"
    assert watch_a.reason_codes == (
        "consensus_ratio_watch",
        "neutral_team_signal_present",
    )
    assert tuple(row.team_id for row in watch_a.rows) == (
        "sports_other",
        "crypto_btc",
        "politics",
    )


def test_empty_input_blocks_as_insufficient_team_coverage() -> None:
    report = _build_report()

    assert report.status == "block"
    assert report.team_count == d("0")
    assert report.category_count == d("0")
    assert report.aligned_team_count == d("0")
    assert report.conflicting_team_count == d("0")
    assert report.review_required_count == d("0")
    assert report.dominant_signal_direction is None
    assert report.consensus_ratio == d("0.000000")
    assert report.conflict_strength == d("0.000000")
    assert report.review_need_score == d("1.000000")
    assert report.average_confidence_score is None
    assert report.reason_codes == ("insufficient_team_coverage",)
    assert report.rows == ()


def test_datetimes_decimals_flags_uniqueness_and_taxonomy_are_validated() -> None:
    module = api()
    local_observed_at = datetime(
        2026,
        7,
        7,
        7,
        0,
        tzinfo=timezone(timedelta(hours=-4)),
    )
    report = _build_report(
        _signal(
            "politics",
            category_id="politics",
            signal_direction="supports_yes",
            signal_strength=d("0.900000"),
            confidence_score=d("0.900000"),
            observed_at=local_observed_at,
        ),
        _signal(
            "crypto_btc",
            category_id="finance.crypto.btc",
            signal_direction="supports_yes",
            signal_strength=d("0.800000"),
            confidence_score=d("0.800000"),
        ),
        _signal(
            "sports_other",
            category_id="sports.other",
            signal_direction="supports_yes",
            signal_strength=d("0.700000"),
            confidence_score=d("0.700000"),
        ),
    )

    assert report.rows[2].observed_at == OBSERVED_AT
    assert type(report.team_count) is Decimal
    assert type(report.consensus_ratio) is Decimal
    assert type(report.rows[0].signal_strength) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.rows[0].alignment_status = "review"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="signal_strength must be a Decimal"):
        _signal(
            "politics",
            category_id="politics",
            signal_direction="supports_yes",
            signal_strength=_DecimalSubclass("0.900000"),
            confidence_score=d("0.900000"),
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        _signal(
            "politics",
            category_id="politics",
            signal_direction="supports_yes",
            signal_strength=d("0.900000"),
            confidence_score=d("0.900000"),
            observed_at=datetime(2026, 7, 7, 11, 0),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_multiteam_signal_consensus_report(
            (),
            config=module.ResearchMultiteamSignalConsensusConfig(),
            generated_at=datetime(2026, 7, 7, 12, 0),
        )
    with pytest.raises(ValueError, match="observed_at must be <= generated_at"):
        _build_report(
            _signal(
                "politics",
                category_id="politics",
                signal_direction="supports_yes",
                signal_strength=d("0.900000"),
                confidence_score=d("0.900000"),
                observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="team_id values must be unique"):
        _build_report(
            _signal(
                "politics",
                category_id="politics",
                signal_direction="supports_yes",
                signal_strength=d("0.900000"),
                confidence_score=d("0.900000"),
            ),
            _signal(
                "politics",
                category_id="politics",
                signal_direction="supports_no",
                signal_strength=d("0.900000"),
                confidence_score=d("0.900000"),
            ),
        )
    with pytest.raises(ValueError, match="category_id must match team_id"):
        _signal(
            "crypto_btc",
            category_id="politics",
            signal_direction="supports_yes",
            signal_strength=d("0.900000"),
            confidence_score=d("0.900000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(
            _signal(
                "politics",
                category_id="politics",
                signal_direction="supports_yes",
                signal_strength=d("0.900000"),
                confidence_score=d("0.900000"),
            ),
            paper_only=False,
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        _signal(
            "politics",
            category_id="politics",
            signal_direction="supports_yes",
            signal_strength=d("0.900000"),
            confidence_score=d("0.900000"),
            observed_at=datetime(2026, 7, 7, 11, 0, tzinfo=_MissingOffsetTz()),
        )
    with pytest.raises(ValueError, match="public payload contains unsafe text"):
        module.ResearchMultiteamSignalConsensusConfig(
            config_version="alpha-token",
        )


def test_payload_helper_is_json_ready_decimal_only_and_sanitized() -> None:
    module = api()
    report = _build_report(
        _signal(
            "politics",
            category_id="politics",
            signal_direction="supports_yes",
            signal_strength=d("0.900000"),
            confidence_score=d("0.900000"),
        ),
        _signal(
            "crypto_btc",
            category_id="finance.crypto.btc",
            signal_direction="supports_yes",
            signal_strength=d("0.800000"),
            confidence_score=d("0.800000"),
        ),
        _signal(
            "sports_other",
            category_id="sports.other",
            signal_direction="supports_yes",
            signal_strength=d("0.700000"),
            confidence_score=d("0.700000"),
        ),
    )

    payload = module.research_multiteam_signal_consensus_report_to_payload(report)

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["team_count"] == "3"
    assert payload["consensus_ratio"] == "1.000000"
    assert payload["rows"][0]["signal_weight"] == "0.640000"
    assert _float_paths(payload) == ()
    assert _unsafe_public_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_public_api_and_module_scope_stay_pure_in_memory_report_only() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_MULTITEAM_SIGNAL_CONSENSUS_CONFIG_VERSION",
        "ResearchMultiteamSignal",
        "ResearchMultiteamSignalConsensusConfig",
        "ResearchMultiteamSignalConsensusReport",
        "ResearchMultiteamSignalConsensusTeamRow",
        "build_research_multiteam_signal_consensus_report",
        "research_multiteam_signal_consensus_report_to_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "wallet",
        "order",
        "buy",
        "sell",
        "position",
        "recommend",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
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


def _float_paths(value: object, prefix: str = "") -> tuple[str, ...]:
    if isinstance(value, float):
        return (prefix or "<root>",)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, nested in value.items():
            child = str(key) if not prefix else f"{prefix}.{key}"
            paths.extend(_float_paths(nested, child))
        return tuple(paths)
    if isinstance(value, list | tuple):
        paths = []
        for index, nested in enumerate(value):
            child = str(index) if not prefix else f"{prefix}.{index}"
            paths.extend(_float_paths(nested, child))
        return tuple(paths)
    return ()


def _unsafe_public_paths(value: object, prefix: str = "") -> tuple[str, ...]:
    fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "token",
        "buy",
        "sell",
        "position",
        "recommend",
    )
    paths: list[str] = []
    if isinstance(value, str):
        lowered = value.lower()
        if any(fragment in lowered for fragment in fragments):
            return (prefix or "<root>",)
        return ()
    if isinstance(value, dict):
        for key, nested in value.items():
            child = str(key) if not prefix else f"{prefix}.{key}"
            lowered_key = str(key).lower()
            if any(fragment in lowered_key for fragment in fragments):
                paths.append(child)
            paths.extend(_unsafe_public_paths(nested, child))
        return tuple(paths)
    if isinstance(value, list | tuple):
        for index, nested in enumerate(value):
            child = str(index) if not prefix else f"{prefix}.{index}"
            paths.extend(_unsafe_public_paths(nested, child))
        return tuple(paths)
    return ()
