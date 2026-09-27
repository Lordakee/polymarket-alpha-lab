"""Deterministic-safe engine port selection for native PostgreSQL tests.

CI root cause this module fixes: tests used to acquire engine ports via
``socket.bind(('127.0.0.1', 0))``, which asks the kernel for any free port —
on Linux the kernel always answers from the ephemeral range (default
``32768-60999``). GitHub ``ubuntu-24.04`` runners have constant outbound HTTPS
churn that consumes ephemeral ports, so between the test's probe and the
PostgreSQL engine start seconds later the chosen port was frequently claimed
by an unrelated outbound socket, surfacing as ``project_postgres_port_in_use``
failures across native lanes (budget_native, uncapped_native,
resolution_native and distribution_native's packaged recipe). Production is
unaffected: the default engine port 55432 sits outside the ephemeral range,
and a quiet development server never reproduces the race.

Fix: draw ports uniformly at random from ``[20000, 32767]`` — strictly below
the Linux ephemeral minimum (32768) and the Windows one (49152) — so an OS
outbound socket can never allocate the chosen port. Each candidate is
verified with a real ``bind`` on ``('127.0.0.1', candidate)`` with
``SO_REUSEADDR`` explicitly disabled: a probe that could succeed over an
occupied port (or that drew from the ephemeral range) would recreate the very
race being fixed. Up to ``MAX_ATTEMPTS`` candidates are tried before failing
loudly. Pure stdlib; no application imports.
"""

import random
import socket

PORT_LOW = 20000
PORT_HIGH = 32767  # Inclusive; strictly below Linux's default ephemeral minimum 32768.
MAX_ATTEMPTS = 64


def pick_port() -> int:
    """Return a bind-verified port in [PORT_LOW, PORT_HIGH] for a native engine.

    The range lies outside every default ephemeral allocation window (Linux
    32768-60999, Windows 49152-65535), so CI runner outbound sockets cannot
    steal the port between this probe and the engine start. Raises RuntimeError
    when no candidate binds.
    """
    for _ in range(MAX_ATTEMPTS):
        candidate = random.randint(PORT_LOW, PORT_HIGH)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
            try:
                probe.bind(('127.0.0.1', candidate))
            except OSError:
                continue
        return candidate
    raise RuntimeError(
        'native test port selection failed: none of %d random candidates in '
        '[%d, %d] could be bound on 127.0.0.1' % (MAX_ATTEMPTS, PORT_LOW, PORT_HIGH)
    )
