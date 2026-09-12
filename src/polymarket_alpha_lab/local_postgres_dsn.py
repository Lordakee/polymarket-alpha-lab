"""Canonical native-PostgreSQL import; retain the single audited implementation.

The historical module name is an API compatibility surface, not a Supabase
runtime dependency. Do not fork or weaken the shared DSN validation logic.
"""
from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn

__all__ = ('validate_local_postgres_dsn',)
