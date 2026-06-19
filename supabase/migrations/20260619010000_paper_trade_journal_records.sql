create table if not exists public.paper_trade_journal_records (
  record_sha256 text primary key
    check (record_sha256 ~ '^[a-f0-9]{64}$'),
  packet_id text not null,
  decision_timestamp_utc timestamptz not null,
  condition_id text not null,
  token_id text not null,
  market_slug text not null,
  outcome_name text not null,
  order_side text not null
    check (order_side in ('buy', 'sell')),
  fill_status text not null
    check (fill_status in ('complete', 'partial')),
  fill_filled_size numeric not null
    check (fill_filled_size > 0),
  fill_average_price numeric not null
    check (fill_average_price >= 0 and fill_average_price <= 1),
  account_equity_before_trade numeric not null
    check (account_equity_before_trade > 0),
  payload_json jsonb not null
    check (jsonb_typeof(payload_json) = 'object'),
  paper_only boolean not null default true
    check (paper_only is true),
  inserted_at timestamptz not null default now()
);

create index if not exists idx_ptjr_decision_timestamp
  on public.paper_trade_journal_records (decision_timestamp_utc desc);

create index if not exists idx_ptjr_condition_decision
  on public.paper_trade_journal_records (condition_id, decision_timestamp_utc desc);

create index if not exists idx_ptjr_token_decision
  on public.paper_trade_journal_records (token_id, decision_timestamp_utc desc);

create index if not exists idx_ptjr_market_slug_decision
  on public.paper_trade_journal_records (market_slug, decision_timestamp_utc desc);

create index if not exists idx_ptjr_payload_json_gin
  on public.paper_trade_journal_records using gin (payload_json jsonb_path_ops);
