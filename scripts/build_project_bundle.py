"""Build a clean Windows kit from committed code and trusted PostgreSQL 17 files."""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from polymarket_alpha_lab.project_postgres.distribution import build_distribution
from polymarket_alpha_lab.project_postgres.files import ProjectDatabaseError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-prefix', required=True, type=Path, help='explicitly trusted native bin/lib/share prefix')
    parser.add_argument('--output', required=True, type=Path, help='new ZIP path; existing outputs are never overwritten')
    args = parser.parse_args(argv)
    try:
        print(json.dumps(build_distribution(ROOT, args.native_prefix, args.output), sort_keys=True))
        return 0
    except ProjectDatabaseError as error:
        code = str(error)
    except Exception:
        code = 'project_bundle_build_failed'
    print(json.dumps({'status': 'blocked', 'reason_code': code}), file=sys.stderr)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
