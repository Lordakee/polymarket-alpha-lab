create table if not exists public.paper_recommendation_reason_trend_health_reports (
  report_sha256 text primary key
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
  generated_at timestamptz not null,
  config_version text not null,
  health_status text not null
    check (health_status in ('pass', 'watch', 'blocked')),
  source_report_count integer not null
    check (source_report_count >= 0),
  reason_code_count integer not null
    check (reason_code_count >= 0),
  blocked_status_count integer not null
    check (blocked_status_count >= 0),
  blocked_status_share numeric
    check (blocked_status_share is null or (blocked_status_share >= 0 and blocked_status_share <= 1)),
  reject_status_count integer not null
    check (reject_status_count >= 0),
  reject_status_share numeric
    check (reject_status_share is null or (reject_status_share >= 0 and reject_status_share <= 1)),
  new_reason_code_count integer not null
    check (new_reason_code_count >= 0),
  transition_count integer not null
    check (transition_count >= 0),
  persistent_reason_codes jsonb not null default '[]'::jsonb
    check (jsonb_typeof(persistent_reason_codes) = 'array'),
  reason_codes jsonb not null default '[]'::jsonb
    check (jsonb_typeof(reason_codes) = 'array'),
  max_blocked_status_share numeric not null
    check (max_blocked_status_share >= 0 and max_blocked_status_share <= 1),
  max_reject_status_share numeric not null
    check (max_reject_status_share >= 0 and max_reject_status_share <= 1),
  max_new_reason_code_count integer not null
    check (max_new_reason_code_count >= 0),
  max_transition_count integer not null
    check (max_transition_count >= 0),
  payload jsonb not null
    check (jsonb_typeof(payload) = 'object'),
  paper_only boolean not null default true
    check (paper_only is true),
  report_only boolean not null default true
    check (report_only is true),
  readonly boolean not null default true
    check (readonly is true),
  inserted_at timestamptz not null default now(),
  check (reason_code_count = jsonb_array_length(reason_codes)),
  check (jsonb_array_length(persistent_reason_codes) <= reason_code_count),
  check (
    (
      reason_code_count = 0
      and blocked_status_count = 0
      and blocked_status_share is null
      and reject_status_count = 0
      and reject_status_share is null
    )
    or (
      reason_code_count > 0
      and blocked_status_share is not null
      and reject_status_share is not null
    )
  ),
  check (
    source_report_count > 0
    or (
      health_status = 'blocked'
      and reason_code_count = 0
      and blocked_status_count = 0
      and blocked_status_share is null
      and reject_status_count = 0
      and reject_status_share is null
      and new_reason_code_count = 0
      and transition_count = 0
      and jsonb_array_length(persistent_reason_codes) = 0
      and jsonb_array_length(reason_codes) = 0
    )
  )
);

create index if not exists idx_prrthr_generated_at
  on public.paper_recommendation_reason_trend_health_reports (generated_at desc);

create index if not exists idx_prrthr_config_version_generated_at
  on public.paper_recommendation_reason_trend_health_reports (config_version, generated_at desc);

create index if not exists idx_prrthr_health_status_generated_at
  on public.paper_recommendation_reason_trend_health_reports (health_status, generated_at desc);

create index if not exists idx_prrthr_reason_codes_gin
  on public.paper_recommendation_reason_trend_health_reports using gin (reason_codes jsonb_path_ops);

create index if not exists idx_prrthr_payload_gin
  on public.paper_recommendation_reason_trend_health_reports using gin (payload jsonb_path_ops);
