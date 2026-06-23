create table if not exists public.paper_recommendation_quality_history_reports (
  report_sha256 text primary key
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
  generated_at timestamptz not null,
  config_version text not null,
  history_status text not null
    check (history_status in ('pass', 'watch', 'blocked')),
  source_report_count integer not null
    check (source_report_count >= 0),
  first_source_generated_at timestamptz null,
  latest_source_generated_at timestamptz null,
  summary_status_rows_json jsonb not null default '[]'::jsonb
    check (jsonb_typeof(summary_status_rows_json) = 'array'),
  pass_summary_count integer not null
    check (pass_summary_count >= 0),
  watch_summary_count integer not null
    check (watch_summary_count >= 0),
  blocked_summary_count integer not null
    check (blocked_summary_count >= 0),
  incomplete_summary_count integer not null
    check (incomplete_summary_count >= 0),
  duplicate_generated_at_count integer not null
    check (duplicate_generated_at_count >= 0),
  recurring_blocked_reason_codes_json jsonb not null default '[]'::jsonb
    check (jsonb_typeof(recurring_blocked_reason_codes_json) = 'array'),
  recurring_incomplete_subreports_json jsonb not null default '[]'::jsonb
    check (jsonb_typeof(recurring_incomplete_subreports_json) = 'array'),
  recurring_incomplete_subreport_count integer not null
    check (recurring_incomplete_subreport_count >= 0),
  reason_codes_json jsonb not null default '[]'::jsonb
    check (jsonb_typeof(reason_codes_json) = 'array'),
  reason_code_count integer not null
    check (reason_code_count > 0),
  payload_json jsonb not null
    check (jsonb_typeof(payload_json) = 'object'),
  paper_only boolean not null default true
    check (paper_only is true),
  report_only boolean not null default true
    check (report_only is true),
  readonly boolean not null default true
    check (readonly is true),
  inserted_at timestamptz not null default now(),
  check (jsonb_array_length(summary_status_rows_json) = 4),
  check (source_report_count = pass_summary_count + watch_summary_count + blocked_summary_count + incomplete_summary_count),
  check (reason_code_count = jsonb_array_length(reason_codes_json)),
  check (recurring_incomplete_subreport_count = jsonb_array_length(recurring_incomplete_subreports_json)),
  check (
    (
      source_report_count = 0
      and first_source_generated_at is null
      and latest_source_generated_at is null
    )
    or (
      source_report_count > 0
      and first_source_generated_at is not null
      and latest_source_generated_at is not null
      and first_source_generated_at <= latest_source_generated_at
    )
  )
);

create index if not exists idx_prqhr_generated_at
  on public.paper_recommendation_quality_history_reports (generated_at desc);

create index if not exists idx_prqhr_config_version_generated_at
  on public.paper_recommendation_quality_history_reports (config_version, generated_at desc);

create index if not exists idx_prqhr_history_status_generated_at
  on public.paper_recommendation_quality_history_reports (history_status, generated_at desc);

create index if not exists idx_prqhr_recurring_blocked_reason_codes_json
  on public.paper_recommendation_quality_history_reports using gin (recurring_blocked_reason_codes_json jsonb_path_ops);

create index if not exists idx_prqhr_reason_codes_json
  on public.paper_recommendation_quality_history_reports using gin (reason_codes_json jsonb_path_ops);

create index if not exists idx_prqhr_payload_json
  on public.paper_recommendation_quality_history_reports using gin (payload_json jsonb_path_ops);
