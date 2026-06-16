"""Entry shim so ``python -m polymarket_alpha_lab ...`` works.

Without this module (and the ``__main__`` guard in :mod:`cli`),
``python -m polymarket_alpha_lab.cli`` imported :func:`cli.main` but never
called it, producing empty output with exit 0.
"""

import sys

from polymarket_alpha_lab.cli import main

if __name__ == "__main__":
    sys.exit(main())
