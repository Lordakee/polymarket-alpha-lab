"""Native project-private PostgreSQL management; never prints a DSN or password."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .files import ProjectDatabaseError
from .runtime import import_runtime_archive, import_runtime_directory
from .server import ProjectPostgres


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True, help='explicit project root; never inferred from a DSN')
    sub = parser.add_subparsers(dest='action', required=True)
    install = sub.add_parser('install-runtime', help='import trusted native binaries, not a service or existing data')
    source = install.add_mutually_exclusive_group(required=True)
    source.add_argument('--from-directory', type=Path, help='explicitly trusted portable prefix containing bin/lib/share')
    source.add_argument('--archive', type=Path, help='official pgsql ZIP; requires an independently approved SHA256')
    install.add_argument('--sha256')
    init = sub.add_parser('init', help='create fresh private cluster, roles and all locked migrations; stop afterward')
    init.add_argument('--port', type=int, default=55432)
    for name in ('up', 'down', 'status', 'migrate'):
        sub.add_parser(name)
    args = parser.parse_args(argv)
    if args.action == 'install-runtime' and bool(args.archive) != bool(args.sha256):
        parser.error('--sha256 is required only with --archive')
    try:
        if args.action == 'install-runtime':
            if args.archive:
                version = import_runtime_archive(args.root, args.archive, expected_sha256=args.sha256)
            else:
                version = import_runtime_directory(args.root, args.from_directory)
            result = {'status': 'runtime_installed', 'version': version}
        else:
            db = ProjectPostgres(args.root)
            result = db.initialize(port=args.port) if args.action == 'init' else getattr(db, args.action)()
        print(json.dumps(result, sort_keys=True))
        return 0
    except ProjectDatabaseError as error:
        print(json.dumps({'status': 'blocked', 'reason_code': str(error)}), file=sys.stderr)
        return 1
    except Exception:
        print(json.dumps({'status': 'blocked', 'reason_code': 'project_postgres_operation_failed'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
