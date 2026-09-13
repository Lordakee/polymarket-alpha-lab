"""Prepare/check the project's private native DB. No models, downloads or trades."""
from pathlib import Path
import argparse
import json
import sys

# Always use THIS extracted project's code, not another editable installation.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from polymarket_alpha_lab.project_postgres.bootstrap import prepare_project
from polymarket_alpha_lab.project_postgres.files import ProjectDatabaseError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=None, help='initial port only; existing port cannot be changed')
    args = parser.parse_args(argv)
    try:
        result = prepare_project(ROOT, port=args.port)
        print(json.dumps(result, sort_keys=True))
        return 0
    except ProjectDatabaseError as error:
        code = str(error)
    except Exception:
        code = 'project_start_failed'
    print(json.dumps({'status': 'blocked', 'reason_code': code}), file=sys.stderr)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
