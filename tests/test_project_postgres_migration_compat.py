"""Preserve the original migration while verifying exact effective native SQL."""
from hashlib import sha256
from pathlib import Path

import pytest

from polymarket_alpha_lab.project_postgres.files import ProjectDatabaseError
from polymarket_alpha_lab.project_postgres import migration_compat as compat
from polymarket_alpha_lab.project_postgres.sql import migration_catalog
from polymarket_alpha_lab.project_postgres.files import Layout

ROOT = Path(__file__).resolve().parents[1]


def original():
    return (ROOT / 'supabase/migrations' / compat.JSONPATH_MIGRATION).read_bytes()


def test_only_one_exact_expression_is_repaired_and_both_hashes_are_verified():
    raw = original()
    assert sha256(raw).hexdigest() == compat.ORIGINAL_SHA256
    effective = compat.native_migration_bytes(compat.JSONPATH_MIGRATION, raw)
    assert effective == raw.replace(b'type(@.reason_codes)', b'@.reason_codes.type()')
    assert sha256(effective).hexdigest() == compat.NATIVE_SHA256
    assert effective.count(b'check (') == raw.count(b'check (')
    assert b'!exists(@.reason_codes)' in effective
    assert b'!= "array"' in effective
    assert original() == raw


@pytest.mark.parametrize('raw', [b'', b'changed', b'type(@.reason_codes)', 'not bytes'])
def test_native_repair_does_not_guess_for_changed_source(raw):
    with pytest.raises(ProjectDatabaseError, match='source_conflict'):
        compat.native_migration_bytes(compat.JSONPATH_MIGRATION, raw)


def test_effective_digest_cannot_silently_change(monkeypatch):
    monkeypatch.setattr(compat, 'NATIVE_SHA256', '0' * 64)
    with pytest.raises(ProjectDatabaseError, match='effective_conflict'):
        compat.native_migration_bytes(compat.JSONPATH_MIGRATION, original())


def test_other_migration_bytes_are_never_rewritten():
    raw = b'-- type(@.reason_codes) is unrelated here\nSELECT 1;'
    assert compat.native_migration_bytes('other.sql', raw) is raw


def test_native_ledger_receipt_uses_effective_digest_not_original():
    rows = migration_catalog(Layout(ROOT))
    row = next(row for row in rows if row[0] == compat.JSONPATH_MIGRATION)
    assert row[1] == compat.NATIVE_SHA256 and row[1] != compat.ORIGINAL_SHA256
    assert b'@.reason_codes.type()' in row[2].encode()
