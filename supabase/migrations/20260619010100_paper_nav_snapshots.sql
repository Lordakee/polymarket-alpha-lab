create table if not exists public.paper_nav_snapshots (
  snapshot_sha256 text primary key
    check (snapshot_sha256 ~ '^[a-f0-9]{64}$'),
  marked_at timestamptz not null,
  starting_cash numeric not null
    check (starting_cash > 0),
  cash_balance numeric not null
    check (cash_balance >= 0),
  exit_nav numeric not null
    check (exit_nav >= 0),
  midpoint_nav numeric
    check (midpoint_nav is null or midpoint_nav >= 0),
  total_cost_basis numeric not null
    check (total_cost_basis >= 0),
  unrealized_exit_pnl numeric not null,
  mark_count integer not null
    check (mark_count >= 0),
  payload_json jsonb not null
    check (jsonb_typeof(payload_json) = 'object'),
  paper_only boolean not null default true
    check (paper_only is true),
  inserted_at timestamptz not null default now()
);

create index if not exists idx_pns_marked_at_snapshot_sha256
  on public.paper_nav_snapshots (marked_at desc, snapshot_sha256 desc);

create index if not exists idx_pns_mark_count_marked_at
  on public.paper_nav_snapshots (mark_count, marked_at desc);

create index if not exists idx_pns_payload_json_gin
  on public.paper_nav_snapshots using gin (payload_json jsonb_path_ops);
