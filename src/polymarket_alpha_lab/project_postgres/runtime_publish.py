"""Bounded publication of an already verified, project-owned engine directory.

Only the final rename is retried. This does not retry copying, native version
probes, database initialization or research. The caller holds Layout.lock().
No ACL changes, process termination, antivirus exclusions or replacing moves.
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import stat
from time import sleep

from .files import Layout, fail, no_links, private_directory

# Error 5 may also be a permanent denial. Never infer its cause or wait forever.
_RETRYABLE_WINERRORS = frozenset((5, 32, 33))
RETRY_DELAYS = (0.1, 0.2, 0.4, 0.8, 1.6, 2.0)


def _identity(path: Path) -> tuple[int, int]:
    no_links(path)
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode):
        fail('project_postgres_runtime_publish_changed')
    return info.st_dev, info.st_ino


def _absent(path: Path) -> None:
    no_links(path)
    try:
        path.lstat()
    except FileNotFoundError:
        return
    fail('project_postgres_runtime_already_installed')


def publish_runtime(layout: Layout, staging: Path, *,
                    validate: Callable[[Path], None], windows: bool) -> None:
    """Rename with at most seven Windows attempts and 5.1s requested sleep.

    Filesystem/validation work adds time: this is not a wall-clock deadline.
    Recheck identity, permissions, destination absence and verified bytes before
    every attempt. Non-Windows rename failures are never retried. Same-user/admin
    mutation is outside the private-instance security boundary; the OS lease
    excludes cooperating project managers. Windows rename itself never replaces
    an existing destination. Failure leaves owned staging for diagnosis.
    """
    if staging != layout.runtime.with_name('postgres.installing'):
        fail('project_postgres_runtime_publish_changed')
    try:
        parent_identity = _identity(staging.parent)
        staging_identity = _identity(staging)
        delays = RETRY_DELAYS if windows else ()
        for attempt in range(len(delays) + 1):
            if (_identity(staging.parent) != parent_identity
                    or _identity(staging) != staging_identity):
                fail('project_postgres_runtime_publish_changed')
            private_directory(staging.parent)
            private_directory(staging)
            _absent(layout.runtime)
            validate(staging)
            # A second absence check catches a destination introduced during
            # validation. Do not use replace(), shutil.move(), or delete first.
            _absent(layout.runtime)
            try:
                staging.rename(layout.runtime)
            except OSError as error:
                if not windows or getattr(error, 'winerror', None) not in _RETRYABLE_WINERRORS:
                    fail('project_postgres_runtime_publish_failed')
                if attempt == len(delays):
                    fail('project_postgres_runtime_publish_blocked')
                sleep(delays[attempt])
                continue
            if _identity(layout.runtime) != staging_identity:
                fail('project_postgres_runtime_publish_changed')
            private_directory(layout.runtime)
            validate(layout.runtime)
            return
    except OSError:
        fail('project_postgres_runtime_publish_failed')
