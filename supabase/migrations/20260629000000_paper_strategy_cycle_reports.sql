create table if not exists public.paper_strategy_cycle_reports (
  report_sha256 text primary key
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
  generated_at timestamptz not null,
  config_version text not null,
  scan_market_count integer not null
    check (scan_market_count >= 0),
  considered_count integer not null
    check (considered_count >= 0),
  snapshot_ready_count integer not null
    check (snapshot_ready_count >= 0),
  cost_aware_report_count integer not null
    check (cost_aware_report_count >= 0),
  blocked_counts_json jsonb not null
    check (jsonb_typeof(blocked_counts_json) = 'array'),
  payload_json jsonb not null
    check (jsonb_typeof(payload_json) = 'object'),
  paper_only boolean not null default true
    check (paper_only is true),
  report_only boolean not null default true
    check (report_only is true),
  inserted_at timestamptz not null default now(),
  check (snapshot_ready_count <= considered_count),
  check (considered_count <= scan_market_count),
  check (cost_aware_report_count = snapshot_ready_count),
  check (payload_json ? 'paper_only' and (payload_json ->> 'paper_only')::boolean is true),
  check (payload_json ? 'report_only' and (payload_json ->> 'report_only')::boolean is true),
  check (payload_json ? 'generated_at' and (payload_json ->> 'generated_at')::timestamptz = generated_at),
  check (payload_json ? 'config_version' and payload_json ->> 'config_version' = config_version),
  check (payload_json ? 'scan_market_count' and (payload_json ->> 'scan_market_count')::integer = scan_market_count),
  check (payload_json ? 'considered_count' and (payload_json ->> 'considered_count')::integer = considered_count),
  check (payload_json ? 'snapshot_ready_count' and (payload_json ->> 'snapshot_ready_count')::integer = snapshot_ready_count),
  check (payload_json ? 'cost_aware_report_count' and (payload_json ->> 'cost_aware_report_count')::integer = cost_aware_report_count),
  check (payload_json ? 'blocked_counts' and blocked_counts_json = payload_json -> 'blocked_counts')
);

create index if not exists idx_pscr_generated_at
  on public.paper_strategy_cycle_reports (generated_at desc);

create index if not exists idx_pscr_config_version_generated_at
  on public.paper_strategy_cycle_reports (config_version, generated_at desc);

create index if not exists idx_pscr_blocked_counts_json_gin
  on public.paper_strategy_cycle_reports using gin (blocked_counts_json jsonb_path_ops);

create index if not exists idx_pscr_payload_json_gin
  on public.paper_strategy_cycle_reports using gin (payload_json jsonb_path_ops);

create index if not exists idx_pscr_load_generated_inserted_sha
  on public.paper_strategy_cycle_reports (generated_at desc, inserted_at desc, report_sha256 desc);
