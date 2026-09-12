"""Exact native bootstrap repair for an invalid historical JSONPath expression.

Never rewrite the historical SQL file or alter an already-applied migration.
Both source and effective SQL bytes are pinned; the native migration ledger
stores the EFFECTIVE digest. Other migrations are returned byte-for-byte.
"""
from hashlib import sha256

from .files import fail

JSONPATH_MIGRATION = '20260622000007_paper_project_screening_rank_stability_reports.sql'
ORIGINAL_SHA256 = 'd8f1ac55812b8d88350968401c902e8f7a0032101baa54323cad94f99dbe2bc4'
NATIVE_SHA256 = 'c3e6aed0861d6e5c332f14823845d4d7fd464440439d9136ddc9f82c23dbce0a'


def native_migration_bytes(name: str, raw: bytes) -> bytes:
    """A closed one-expression repair, not an arbitrary migration rewrite API."""
    if name != JSONPATH_MIGRATION:
        return raw
    if type(raw) is not bytes or sha256(raw).hexdigest() != ORIGINAL_SHA256:
        fail('project_postgres_native_migration_source_conflict')
    # PostgreSQL JSONPath exposes type() as an item method, not type(item).
    # Preserve the missing-field and non-array rejection; do not remove CHECK.
    original = b'type(@.reason_codes)'
    if raw.count(original) != 1:
        fail('project_postgres_native_migration_source_conflict')
    effective = raw.replace(original, b'@.reason_codes.type()')
    if sha256(effective).hexdigest() != NATIVE_SHA256:
        fail('project_postgres_native_migration_effective_conflict')
    return effective
