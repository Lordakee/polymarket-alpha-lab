"""Explicit first launch for a trusted native kit. No network, models or reset."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from .distribution import ENGINE, MANIFEST, require_windows, verify_distribution
from .files import Layout, fail, no_links
from .runtime import import_runtime_archive, verify_runtime
from .server import ProjectPostgres
from .sql import server_configuration


def prepare_project(root: Path, *, port: int | None = None) -> dict:
    """Import the bundled engine if absent; initialize ONLY a fresh project.

    Existing native imports also work in source checkouts without a kit. A
    partial home/runtime is an error, never a reason to clear data or reinstall.
    The default port is chosen only on initial creation. A different explicit
    port on an existing instance is refused, not silently applied or ignored.
    """
    if port is not None:
        server_configuration(port)
    layout = Layout(root)
    seed, manifest_path = layout.root / ENGINE, layout.root / MANIFEST
    no_links(seed)
    no_links(manifest_path)
    manifest = None
    if manifest_path.exists() or seed.exists():
        manifest = verify_distribution(layout.root)
        require_windows()
    # Fail before creating a cluster when the Python DB driver is unavailable.
    if importlib.util.find_spec('psycopg') is None:
        fail('project_start_postgres_extra_required')
    no_links(layout.runtime)
    if not layout.runtime.exists():
        if layout.home.exists():
            fail('project_start_existing_database_runtime_missing')
        if manifest is None:
            fail('project_start_runtime_or_bundle_required')
        import_runtime_archive(layout.root, seed, expected_sha256=manifest['files'][ENGINE])
    runtime = verify_runtime(layout)
    if manifest is not None and runtime['version'] != manifest['postgres_version']:
        fail('project_start_runtime_version_conflict')
    db = ProjectPostgres(layout.root)
    initialized = False
    # initialize() holds the existing exclusive OS lifecycle lease and refuses
    # a concurrent or previously partial init. No lock stealing/retry is added.
    if not layout.home.exists():
        db.initialize(port=55432 if port is None else port)
        initialized = True
    status = db.status()
    if port is not None and status['port'] != port:
        fail('project_start_existing_port_conflict')
    with db.session() as session:
        report = session.evaluate()  # Strict complete-history, restricted role.
    return dict(status='ready', initialized_here=initialized, postgres_version=runtime['version'],
        port=status['port'], instance_id=status['instance_id'],
        recorded_attempts=len(report.records), confirmed_outcomes=len(report.outcomes),
        public_network_called=False, live_model_called=False,
        source_commit=None if manifest is None else manifest['source_commit'])
