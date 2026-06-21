create table if not exists public.paper_recommendation_risk_budget_reports (
  report_sha256 text primary key
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
  generated_at timestamptz not null,
  config_version text not null,
  status text not null
    check (status in ('pass', 'watch', 'blocked')),
  reason_codes jsonb not null default '[]'::jsonb
    check (jsonb_typeof(reason_codes) = 'array'),
  total_suggested_notional numeric not null
    check (total_suggested_notional >= 0),
  remaining_total_notional numeric null
    check (remaining_total_notional is null or remaining_total_notional >= 0),
  total_notional_utilization numeric null
    check (total_notional_utilization is null or (total_notional_utilization >= 0 and total_notional_utilization <= 1)),
  largest_single_recommendation_share numeric null
    check (largest_single_recommendation_share is null or (largest_single_recommendation_share >= 0 and largest_single_recommendation_share <= 1)),
  selected_count integer not null
    check (selected_count >= 0),
  blocked_count integer not null
    check (blocked_count >= 0),
  nav_notional numeric null
    check (nav_notional is null or nav_notional >= 0),
  max_total_utilization numeric not null
    check (max_total_utilization > 0 and max_total_utilization <= 1),
  max_single_recommendation_share numeric not null
    check (max_single_recommendation_share > 0 and max_single_recommendation_share <= 1),
  min_remaining_notional numeric not null
    check (min_remaining_notional >= 0),
  max_selected_count integer not null
    check (max_selected_count > 0),
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

create index if not exists idx_prrbr_generated_at
  on public.paper_recommendation_risk_budget_reports (generated_at desc);

create index if not exists idx_prrbr_config_version_generated_at
  on public.paper_recommendation_risk_budget_reports (config_version, generated_at desc);

create index if not exists idx_prrbr_status_generated_at
  on public.paper_recommendation_risk_budget_reports (status, generated_at desc);

create index if not exists idx_prrbr_reason_codes_gin
  on public.paper_recommendation_risk_budget_reports using gin (reason_codes jsonb_path_ops);

create index if not exists idx_prrbr_payload_gin
  on public.paper_recommendation_risk_budget_reports using gin (payload jsonb_path_ops);
