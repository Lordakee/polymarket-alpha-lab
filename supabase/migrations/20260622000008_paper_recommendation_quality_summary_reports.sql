create table if not exists public.paper_recommendation_quality_summary_reports (
  report_sha256 text primary key
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
  generated_at timestamptz not null,
  config_version text not null,
  summary_status text not null
    check (summary_status in ('pass', 'watch', 'blocked', 'incomplete')),
  subreport_count integer not null
    check (subreport_count >= 0),
  pass_count integer not null
    check (pass_count >= 0),
  watch_count integer not null
    check (watch_count >= 0),
  blocked_count integer not null
    check (blocked_count >= 0),
  incomplete_count integer not null
    check (incomplete_count >= 0),
  reason_code_counts_json jsonb not null default '[]'::jsonb
    check (jsonb_typeof(reason_code_counts_json) = 'array'),
  reason_codes_json jsonb not null default '[]'::jsonb
    check (jsonb_typeof(reason_codes_json) = 'array'),
  subreports_json jsonb not null default '[]'::jsonb
    check (jsonb_typeof(subreports_json) = 'array'),
  payload_json jsonb not null
    check (jsonb_typeof(payload_json) = 'object'),
  paper_only boolean not null default true
    check (paper_only is true),
  report_only boolean not null default true
    check (report_only is true),
  readonly boolean not null default true
    check (readonly is true),
  inserted_at timestamptz not null default now(),
  check (subreport_count = 5),
  check (subreport_count = pass_count + watch_count + blocked_count + incomplete_count),
  check (subreport_count = jsonb_array_length(subreports_json)),
  check (jsonb_array_length(reason_codes_json) = jsonb_array_length(reason_code_counts_json)),
  check ((subreports_json -> 0 ->> 'report_name') = 'health'),
  check ((subreports_json -> 1 ->> 'report_name') = 'consistency'),
  check ((subreports_json -> 2 ->> 'report_name') = 'risk_budget'),
  check ((subreports_json -> 3 ->> 'report_name') = 'reason_trend'),
  check ((subreports_json -> 4 ->> 'report_name') = 'rank_stability'),
  check (
    pass_count = jsonb_array_length(
      jsonb_path_query_array(subreports_json, '$[*] ? (@.status == "pass")')
    )
  ),
  check (
    watch_count = jsonb_array_length(
      jsonb_path_query_array(subreports_json, '$[*] ? (@.status == "watch")')
    )
  ),
  check (
    blocked_count = jsonb_array_length(
      jsonb_path_query_array(subreports_json, '$[*] ? (@.status == "blocked")')
    )
  ),
  check (
    incomplete_count = jsonb_array_length(
      jsonb_path_query_array(subreports_json, '$[*] ? (@.status == "incomplete")')
    )
  ),
  check (
    (
      summary_status = 'blocked'
      and blocked_count > 0
    )
    or (
      summary_status = 'incomplete'
      and blocked_count = 0
      and incomplete_count > 0
    )
    or (
      summary_status = 'watch'
      and blocked_count = 0
      and incomplete_count = 0
      and watch_count > 0
    )
    or (
      summary_status = 'pass'
      and blocked_count = 0
      and incomplete_count = 0
      and watch_count = 0
    )
  ),
  check ((payload_json ->> 'paper_only') = 'true'),
  check ((payload_json ->> 'report_only') = 'true'),
  check ((payload_json ->> 'readonly') = 'true'),
  check (
    not jsonb_path_exists(
      subreports_json,
      '$[*] ? (@.paper_only != true || @.report_only != true || @.readonly != true)'
    )
  ),
  check (
    not jsonb_path_exists(
      payload_json,
      '$.subreports[*] ? (@.paper_only != true || @.report_only != true || @.readonly != true)'
    )
  )
);

create index if not exists idx_prqsr_generated_at
  on public.paper_recommendation_quality_summary_reports (generated_at desc);

create index if not exists idx_prqsr_config_version_generated_at
  on public.paper_recommendation_quality_summary_reports (config_version, generated_at desc);

create index if not exists idx_prqsr_summary_status_generated_at
  on public.paper_recommendation_quality_summary_reports (summary_status, generated_at desc);

create index if not exists idx_prqsr_reason_codes_json
  on public.paper_recommendation_quality_summary_reports using gin (reason_codes_json jsonb_path_ops);

create index if not exists idx_prqsr_subreports_json
  on public.paper_recommendation_quality_summary_reports using gin (subreports_json jsonb_path_ops);

create index if not exists idx_prqsr_payload_json
  on public.paper_recommendation_quality_summary_reports using gin (payload_json jsonb_path_ops);
