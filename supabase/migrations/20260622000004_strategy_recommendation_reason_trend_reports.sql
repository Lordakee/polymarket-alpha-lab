create table if not exists public.strategy_recommendation_reason_trend_reports (
  report_sha256 text primary key
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
  generated_at timestamptz not null,
  config_version text not null,
  status text not null
    check (status in ('stable', 'watch', 'blocked')),
  source_report_count integer not null
    check (source_report_count >= 0),
  first_generated_at timestamptz null,
  latest_generated_at timestamptz null,
  latest_primary_reason_code_counts jsonb not null default '{}'::jsonb
    check (jsonb_typeof(latest_primary_reason_code_counts) = 'object'),
  total_primary_reason_code_counts jsonb not null default '{}'::jsonb
    check (jsonb_typeof(total_primary_reason_code_counts) = 'object'),
  top_new_reason_codes jsonb not null default '{}'::jsonb
    check (jsonb_typeof(top_new_reason_codes) = 'object'),
  persistent_reason_codes jsonb not null default '[]'::jsonb
    check (jsonb_typeof(persistent_reason_codes) = 'array'),
  latest_reason_code_count integer not null
    check (latest_reason_code_count >= 0),
  latest_no_reason_code_count integer not null
    check (latest_no_reason_code_count >= 0),
  latest_blocked_reason_count integer not null
    check (latest_blocked_reason_count >= 0),
  latest_no_reason_code_share numeric null
    check (latest_no_reason_code_share is null or (latest_no_reason_code_share >= 0 and latest_no_reason_code_share <= 1)),
  latest_blocked_reason_share numeric null
    check (latest_blocked_reason_share is null or (latest_blocked_reason_share >= 0 and latest_blocked_reason_share <= 1)),
  max_blocked_reason_share numeric not null
    check (max_blocked_reason_share >= 0 and max_blocked_reason_share <= 1),
  max_no_reason_code_share numeric not null
    check (max_no_reason_code_share >= 0 and max_no_reason_code_share <= 1),
  top_reason_code_limit integer not null
    check (top_reason_code_limit > 0),
  blocked_reason_codes jsonb not null default '[]'::jsonb
    check (jsonb_typeof(blocked_reason_codes) = 'array'),
  payload jsonb not null
    check (jsonb_typeof(payload) = 'object'),
  paper_only boolean not null default true
    check (paper_only is true),
  report_only boolean not null default true
    check (report_only is true),
  readonly boolean not null default true
    check (readonly is true),
  inserted_at timestamptz not null default now()
);

create index if not exists idx_srrtr_generated_at
  on public.strategy_recommendation_reason_trend_reports (generated_at desc);

create index if not exists idx_srrtr_config_version_generated_at
  on public.strategy_recommendation_reason_trend_reports (config_version, generated_at desc);

create index if not exists idx_srrtr_status_generated_at
  on public.strategy_recommendation_reason_trend_reports (status, generated_at desc);

create index if not exists idx_srrtr_latest_primary_reason_codes_gin
  on public.strategy_recommendation_reason_trend_reports using gin (latest_primary_reason_code_counts jsonb_path_ops);

create index if not exists idx_srrtr_total_primary_reason_codes_gin
  on public.strategy_recommendation_reason_trend_reports using gin (total_primary_reason_code_counts jsonb_path_ops);

create index if not exists idx_srrtr_top_new_reason_codes_gin
  on public.strategy_recommendation_reason_trend_reports using gin (top_new_reason_codes jsonb_path_ops);

create index if not exists idx_srrtr_payload_gin
  on public.strategy_recommendation_reason_trend_reports using gin (payload jsonb_path_ops);
