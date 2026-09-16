"""Test-only fresh-interpreter probe for scripts selecting their own source.

The inserted foreign path models an unrelated editable installation. This is
not a hostile-interpreter sandbox or package authenticity check. No native
engine, network, provider or user database is needed.
"""
from pathlib import Path
import subprocess

from polymarket_alpha_lab.project_postgres.files import clean_environment

ENTRYPOINTS = ('project_database.py', 'review_resolution_queue.py')
_CHILD = r'''
from pathlib import Path
import runpy, sys
root, foreign = map(Path, sys.argv[1:3])
script, arguments = sys.argv[3], sys.argv[4:]
sys.path.insert(0, str(foreign))
sys.argv = [str(root / 'scripts' / script), *arguments]
try:
    runpy.run_path(sys.argv[0], run_name='__main__')
except SystemExit as error:
    code = error.code
else:
    code = 0
loaded = [value for name, value in sys.modules.items()
          if name == 'polymarket_alpha_lab' or name.startswith('polymarket_alpha_lab.')]
assert loaded, 'project modules were not loaded'
for module in loaded:
    assert Path(module.__file__).resolve().is_relative_to(root.resolve() / 'src'), 'foreign project code selected'
print('PROJECT_ENTRY_SOURCE_OK', file=sys.stderr)
raise SystemExit(code)
'''


def probe_entry(root, python, working, *, script, arguments=('--help',)):
    """Use real script bytes, a foreign source decoy and an unrelated cwd."""
    if script not in ENTRYPOINTS:
        raise ValueError('unsupported probe script')
    working = Path(working)
    working.mkdir(parents=True, exist_ok=False)
    foreign = working / 'unrelated-editable' / 'polymarket_alpha_lab'
    foreign.mkdir(parents=True)
    (foreign / '__init__.py').write_text("raise RuntimeError('FOREIGN_EDITABLE_SELECTED')\n", encoding='ascii')
    return subprocess.run([str(python), '-I', '-c', _CHILD, str(root), str(foreign.parent),
                           script, *arguments], cwd=working, env=clean_environment(),
        stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding='utf-8',
        timeout=30, check=False, shell=False)
