"""Tests for the immutable approved BTC evidence source registry."""

import ast
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Final

import pytest

from polymarket_alpha_lab.crypto_btc_evidence_registry import (
    CryptoBtcApprovedSource,
    approved_crypto_btc_source_registry,
    require_approved_crypto_btc_source,
)
from polymarket_alpha_lab import crypto_btc_evidence_registry as registry_module

MODULE_PATH: Final = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "crypto_btc_evidence_registry.py"
)
MODULE_LINE_CEILING: Final = 260

EXPECTED_SOURCE_IDS: Final = (
    "btc_derivatives_reference",
    "btc_onchain_reference",
    "btc_resolution_rules",
    "btc_spot_reference",
)
EXPECTED_SOURCE_FAMILIES: Final = (
    "btc_derivatives",
    "btc_onchain",
    "btc_resolution_rules",
    "btc_spot",
)
EXPECTED_TRUST_TIERS: Final = ("official", "primary")
EXPECTED_FAMILY_AND_TIER_BY_SOURCE_ID: Final = {
    "btc_derivatives_reference": ("btc_derivatives", "primary"),
    "btc_onchain_reference": ("btc_onchain", "primary"),
    "btc_resolution_rules": ("btc_resolution_rules", "official"),
    "btc_spot_reference": ("btc_spot", "primary"),
}
EXPECTED_PUBLIC_ALL: Final = (
    "CryptoBtcApprovedSource",
    "approved_crypto_btc_source_registry",
    "require_approved_crypto_btc_source",
)
UNKNOWN_SOURCE_MESSAGE: Final = "source_id must be a known approved BTC source"


def test_registry_returns_exact_four_entry_sorted_tuple() -> None:
    registry = approved_crypto_btc_source_registry()

    assert type(registry) is tuple
    assert len(registry) == 4
    assert tuple(source.source_id for source in registry) == EXPECTED_SOURCE_IDS
    assert tuple(source.source_id for source in registry) == tuple(
        sorted(source.source_id for source in registry)
    )
    assert len({source.source_id for source in registry}) == 4


def test_registry_entries_carry_pinned_family_tier_and_version() -> None:
    for source in approved_crypto_btc_source_registry():
        expected_family, expected_tier = EXPECTED_FAMILY_AND_TIER_BY_SOURCE_ID[
            source.source_id
        ]
        assert source.source_family == expected_family
        assert source.trust_tier == expected_tier
        assert source.registry_version == registry_module.CRYPTO_BTC_APPROVED_REGISTRY_VERSION
        assert source.registry_version == "crypto-btc-approved-registry-v0"
        assert source.paper_only is True
        assert source.report_only is True
        assert source.readonly is True


def test_module_constants_are_pinned_sorted_and_closed() -> None:
    assert registry_module.CRYPTO_BTC_APPROVED_SOURCE_IDS == EXPECTED_SOURCE_IDS
    assert registry_module.CRYPTO_BTC_APPROVED_SOURCE_IDS == tuple(
        sorted(registry_module.CRYPTO_BTC_APPROVED_SOURCE_IDS)
    )
    assert registry_module.CRYPTO_BTC_SOURCE_FAMILIES == EXPECTED_SOURCE_FAMILIES
    assert registry_module.CRYPTO_BTC_SOURCE_FAMILIES == tuple(
        sorted(registry_module.CRYPTO_BTC_SOURCE_FAMILIES)
    )
    assert len(set(registry_module.CRYPTO_BTC_SOURCE_FAMILIES)) == len(
        registry_module.CRYPTO_BTC_SOURCE_FAMILIES
    )
    assert registry_module.CRYPTO_BTC_TRUST_TIERS == EXPECTED_TRUST_TIERS
    assert registry_module.CRYPTO_BTC_TRUST_TIERS == tuple(
        sorted(registry_module.CRYPTO_BTC_TRUST_TIERS)
    )
    assert len(set(registry_module.CRYPTO_BTC_TRUST_TIERS)) == len(
        registry_module.CRYPTO_BTC_TRUST_TIERS
    )


def test_approved_source_dataclass_is_frozen_slotted_and_final() -> None:
    source = require_approved_crypto_btc_source("btc_spot_reference")

    with pytest.raises(FrozenInstanceError):
        source.source_family = "btc_onchain"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source.paper_only = False  # type: ignore[misc]

    assert not hasattr(source, "__dict__")
    assert CryptoBtcApprovedSource.__slots__ == (
        "source_id",
        "source_family",
        "trust_tier",
        "registry_version",
        "paper_only",
        "report_only",
        "readonly",
    )
    with pytest.raises(TypeError):
        class ImpostorSource(CryptoBtcApprovedSource):  # type: ignore[misc]
            pass


def test_require_lookup_resolves_every_approved_source() -> None:
    registry = approved_crypto_btc_source_registry()
    for source in registry:
        resolved = require_approved_crypto_btc_source(source.source_id)
        assert resolved == source
        assert resolved is not None
        assert hash(resolved) == hash(source)

    assert require_approved_crypto_btc_source("btc_spot_reference").source_id == (
        "btc_spot_reference"
    )


def test_require_lookup_rejects_unknown_and_non_string_ids() -> None:
    for bad_source_id in (
        "",
        "   ",
        "btc_spot_references",
        "BTC_SPOT_REFERENCE",
        "eth_spot_reference",
        "btc_spot",
        "btc_resolution_rulez",
        "btc-spot-reference",
    ):
        with pytest.raises(ValueError, match=UNKNOWN_SOURCE_MESSAGE):
            require_approved_crypto_btc_source(bad_source_id)

    for non_string in (None, 7, 3.5, b"btc_spot_reference", object()):
        with pytest.raises(ValueError, match=UNKNOWN_SOURCE_MESSAGE):
            require_approved_crypto_btc_source(non_string)  # type: ignore[arg-type]


def test_caller_cannot_construct_extra_or_noncanonical_entries() -> None:
    with pytest.raises(ValueError, match=UNKNOWN_SOURCE_MESSAGE):
        CryptoBtcApprovedSource(
            source_id="btc_new_reference",
            source_family="btc_spot",
            trust_tier="primary",
        )

    with pytest.raises(ValueError, match="source_family must match source_id"):
        CryptoBtcApprovedSource(
            source_id="btc_spot_reference",
            source_family="btc_onchain",
            trust_tier="primary",
        )

    with pytest.raises(ValueError, match="trust_tier must match source_id"):
        CryptoBtcApprovedSource(
            source_id="btc_spot_reference",
            source_family="btc_spot",
            trust_tier="official",
        )

    canonical = CryptoBtcApprovedSource(
        source_id="btc_resolution_rules",
        source_family="btc_resolution_rules",
        trust_tier="official",
    )
    assert canonical == require_approved_crypto_btc_source("btc_resolution_rules")


def test_vocabulary_validation_rejects_unknown_family_and_tier() -> None:
    with pytest.raises(ValueError, match="source_family must be a known BTC source family"):
        CryptoBtcApprovedSource(
            source_id="btc_spot_reference",
            source_family="eth_spot",
            trust_tier="primary",
        )

    with pytest.raises(ValueError, match="trust_tier must be a known BTC trust tier"):
        CryptoBtcApprovedSource(
            source_id="btc_spot_reference",
            source_family="btc_spot",
            trust_tier="proxy",
        )

    with pytest.raises(ValueError, match="trust_tier must be a known BTC trust tier"):
        CryptoBtcApprovedSource(
            source_id="btc_onchain_reference",
            source_family="btc_onchain",
            trust_tier="official_and_primary",
        )


def test_registry_version_must_be_the_fixed_literal() -> None:
    with pytest.raises(
        ValueError,
        match="registry_version must be crypto-btc-approved-registry-v0",
    ):
        CryptoBtcApprovedSource(
            source_id="btc_spot_reference",
            source_family="btc_spot",
            trust_tier="primary",
            registry_version="crypto-btc-approved-registry-v1",
        )

    pinned = CryptoBtcApprovedSource(
        source_id="btc_spot_reference",
        source_family="btc_spot",
        trust_tier="primary",
        registry_version="crypto-btc-approved-registry-v0",
    )
    assert pinned == require_approved_crypto_btc_source("btc_spot_reference")


def test_hard_flags_must_be_exact_true() -> None:
    with pytest.raises(ValueError, match="paper_only must be True"):
        CryptoBtcApprovedSource(
            source_id="btc_spot_reference",
            source_family="btc_spot",
            trust_tier="primary",
            paper_only=False,
        )
    with pytest.raises(ValueError, match="report_only must be True"):
        CryptoBtcApprovedSource(
            source_id="btc_spot_reference",
            source_family="btc_spot",
            trust_tier="primary",
            report_only=False,
        )
    with pytest.raises(ValueError, match="readonly must be True"):
        CryptoBtcApprovedSource(
            source_id="btc_spot_reference",
            source_family="btc_spot",
            trust_tier="primary",
            readonly=False,
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        CryptoBtcApprovedSource(
            source_id="btc_spot_reference",
            source_family="btc_spot",
            trust_tier="primary",
            paper_only=1,
        )
    with pytest.raises(ValueError, match="readonly must be True"):
        CryptoBtcApprovedSource(
            source_id="btc_spot_reference",
            source_family="btc_spot",
            trust_tier="primary",
            readonly="yes",
        )


def test_factory_returns_fresh_tuple_and_registry_stays_fixed() -> None:
    first = approved_crypto_btc_source_registry()
    second = approved_crypto_btc_source_registry()

    assert first == second
    assert first is not second
    assert len(first) == 4

    canonical = CryptoBtcApprovedSource(
        source_id="btc_spot_reference",
        source_family="btc_spot",
        trust_tier="primary",
    )
    caller_side_tuple = first + (canonical,)
    assert len(caller_side_tuple) == 5
    assert len(approved_crypto_btc_source_registry()) == 4
    assert approved_crypto_btc_source_registry() == first

    with pytest.raises(ValueError, match=UNKNOWN_SOURCE_MESSAGE):
        require_approved_crypto_btc_source("btc_new_reference")


def test_module_exports_exact_public_surface_with_no_mutation_api() -> None:
    assert registry_module.__all__ == EXPECTED_PUBLIC_ALL
    assert len(set(registry_module.__all__)) == len(registry_module.__all__)

    mutation_tokens = (
        "add_",
        "_add",
        "append",
        "extend",
        "insert",
        "promote",
        "register",
        "remove_",
        "update_",
        "inject",
    )
    for name in vars(registry_module):
        if name.startswith("__"):
            continue
        assert not any(token in name.lower() for token in mutation_tokens), name

    public_callables = {
        name
        for name, value in vars(registry_module).items()
        if not name.startswith("_") and callable(value)
    }
    assert {
        "CryptoBtcApprovedSource",
        "approved_crypto_btc_source_registry",
        "require_approved_crypto_btc_source",
    } <= public_callables
    assert public_callables <= set(EXPECTED_PUBLIC_ALL) | {"dataclass", "final", "Final"}


def test_module_is_pure_stdlib_with_no_floats_or_async_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename="crypto_btc_evidence_registry.py")

    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(not alias.name.startswith(".") for alias in node.names)
            imported_modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imported_modules.add((node.module or "").split(".")[0])
        assert not (isinstance(node, ast.Constant) and type(node.value) is float)
        assert not isinstance(
            node,
            (ast.AsyncFunctionDef, ast.Await, ast.Lambda, ast.Yield, ast.YieldFrom),
        )

    assert imported_modules <= {"__future__", "dataclasses", "typing"}
    assert imported_modules == {"__future__", "dataclasses", "typing"}


def test_module_source_stays_within_line_ceiling() -> None:
    line_count = len(MODULE_PATH.read_text(encoding="utf-8").splitlines())
    assert line_count <= MODULE_LINE_CEILING
