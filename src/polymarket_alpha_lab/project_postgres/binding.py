"""Optional in-transaction identity guard for managed research sessions.

Legacy explicit DSN APIs retain compatibility. Managed sessions never accept a
caller DSN and assert instance identity on EVERY actual research connection.
"""
from contextlib import contextmanager
from contextvars import ContextVar
import os

from .files import fail

_EXPECTED = ContextVar('project_postgres_expected_instance', default=None)


def check_environment() -> None:
    if _EXPECTED.get() is not None and any(k.upper().startswith('PG') for k in os.environ):
        fail('project_postgres_environment_override_rejected')


def verify_connection(cursor) -> None:
    expected = _EXPECTED.get()
    if expected is None:
        return
    cursor.execute("SELECT instance_id,root_sha256,system_identifier,current_database(),current_user "
                   "FROM project_private.instance WHERE singleton IS TRUE")
    if cursor.fetchall() != [(*expected, 'polymarket_alpha_lab', 'pal_app')]:
        fail('project_postgres_connection_identity_mismatch')


@contextmanager
def bound(instance_id: str, root_hash: str, system_id: str):
    token = _EXPECTED.set((instance_id, root_hash, system_id))
    try:
        check_environment()
        yield
    finally:
        _EXPECTED.reset(token)
