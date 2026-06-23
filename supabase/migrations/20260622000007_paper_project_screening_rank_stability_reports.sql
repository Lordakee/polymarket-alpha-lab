create table if not exists public.paper_project_screening_rank_stability_reports (
  report_sha256 text primary key
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
  generated_at timestamptz not null,
  config_version text not null,
  stability_status text not null
    check (stability_status in ('stable', 'watch', 'blocked')),
  reason_codes_json jsonb not null
    check (jsonb_typeof(reason_codes_json) = 'array'),
  source_report_count integer not null
    check (source_report_count >= 0),
  candidate_count integer not null
    check (candidate_count >= 0),
  stable_count integer not null
    check (stable_count >= 0),
  watch_count integer not null
    check (watch_count >= 0),
  blocked_count integer not null
    check (blocked_count >= 0),
  stable_ready_count integer not null
    check (stable_ready_count >= 0),
  unstable_ready_count integer not null
    check (unstable_ready_count >= 0),
  scoring_side_changed_count integer not null
    check (scoring_side_changed_count >= 0),
  source_status_changed_count integer not null
    check (source_status_changed_count >= 0),
  screening_status_changed_count integer not null
    check (screening_status_changed_count >= 0),
  research_bucket_changed_count integer not null
    check (research_bucket_changed_count >= 0),
  latest_generated_at timestamptz null,
  top_stable_market_slug text null,
  rows_json jsonb not null
    check (jsonb_typeof(rows_json) = 'array'),
  payload_json jsonb not null
    check (jsonb_typeof(payload_json) = 'object'),
  paper_only boolean not null default true
    check (paper_only is true),
  report_only boolean not null default true
    check (report_only is true),
  readonly boolean not null default true
    check (readonly is true),
  inserted_at timestamptz not null default now(),
  check (stable_count + watch_count + blocked_count = candidate_count),
  check (stable_ready_count <= stable_count),
  check (unstable_ready_count <= watch_count + blocked_count),
  check (stable_ready_count + unstable_ready_count <= candidate_count),
  check (scoring_side_changed_count <= candidate_count),
  check (source_status_changed_count <= candidate_count),
  check (screening_status_changed_count <= candidate_count),
  check (research_bucket_changed_count <= candidate_count),
  check (jsonb_array_length(rows_json) = candidate_count),
  check (source_report_count > 0 or (candidate_count = 0 and latest_generated_at is null)),
  check (source_report_count = 0 or latest_generated_at is not null),
  check (payload_json ? 'paper_only' and payload_json -> 'paper_only' = 'true'::jsonb),
  check (payload_json ? 'report_only' and payload_json -> 'report_only' = 'true'::jsonb),
  check (payload_json ? 'readonly' and payload_json -> 'readonly' = 'true'::jsonb),
  check (payload_json ? 'generated_at' and jsonb_typeof(payload_json -> 'generated_at') = 'string' and (payload_json ->> 'generated_at')::timestamptz = generated_at),
  check (payload_json ? 'config_version' and jsonb_typeof(payload_json -> 'config_version') = 'string' and payload_json ->> 'config_version' = config_version),
  check (payload_json ? 'stability_status' and jsonb_typeof(payload_json -> 'stability_status') = 'string' and payload_json ->> 'stability_status' = stability_status),
  check (payload_json ? 'source_report_count' and jsonb_typeof(payload_json -> 'source_report_count') = 'number' and (payload_json ->> 'source_report_count')::integer = source_report_count),
  check (payload_json ? 'candidate_count' and jsonb_typeof(payload_json -> 'candidate_count') = 'number' and (payload_json ->> 'candidate_count')::integer = candidate_count),
  check (payload_json ? 'stable_count' and jsonb_typeof(payload_json -> 'stable_count') = 'number' and (payload_json ->> 'stable_count')::integer = stable_count),
  check (payload_json ? 'watch_count' and jsonb_typeof(payload_json -> 'watch_count') = 'number' and (payload_json ->> 'watch_count')::integer = watch_count),
  check (payload_json ? 'blocked_count' and jsonb_typeof(payload_json -> 'blocked_count') = 'number' and (payload_json ->> 'blocked_count')::integer = blocked_count),
  check (payload_json ? 'stable_ready_count' and jsonb_typeof(payload_json -> 'stable_ready_count') = 'number' and (payload_json ->> 'stable_ready_count')::integer = stable_ready_count),
  check (payload_json ? 'unstable_ready_count' and jsonb_typeof(payload_json -> 'unstable_ready_count') = 'number' and (payload_json ->> 'unstable_ready_count')::integer = unstable_ready_count),
  check (payload_json ? 'scoring_side_changed_count' and jsonb_typeof(payload_json -> 'scoring_side_changed_count') = 'number' and (payload_json ->> 'scoring_side_changed_count')::integer = scoring_side_changed_count),
  check (payload_json ? 'source_status_changed_count' and jsonb_typeof(payload_json -> 'source_status_changed_count') = 'number' and (payload_json ->> 'source_status_changed_count')::integer = source_status_changed_count),
  check (payload_json ? 'screening_status_changed_count' and jsonb_typeof(payload_json -> 'screening_status_changed_count') = 'number' and (payload_json ->> 'screening_status_changed_count')::integer = screening_status_changed_count),
  check (payload_json ? 'research_bucket_changed_count' and jsonb_typeof(payload_json -> 'research_bucket_changed_count') = 'number' and (payload_json ->> 'research_bucket_changed_count')::integer = research_bucket_changed_count),
  check (payload_json ? 'reason_codes' and jsonb_typeof(payload_json -> 'reason_codes') = 'array' and payload_json -> 'reason_codes' = reason_codes_json),
  check (payload_json ? 'rows' and jsonb_typeof(payload_json -> 'rows') = 'array' and payload_json -> 'rows' = rows_json),
  check (not jsonb_path_exists(rows_json, '$[*] ? (!exists(@.reason_codes) || type(@.reason_codes) != "array")')),
  check (candidate_count > 0 or (stability_status = 'watch' and stable_count = 0 and watch_count = 0 and blocked_count = 0 and stable_ready_count = 0 and unstable_ready_count = 0 and scoring_side_changed_count = 0 and source_status_changed_count = 0 and screening_status_changed_count = 0 and research_bucket_changed_count = 0 and top_stable_market_slug is null and jsonb_array_length(rows_json) = 0 and reason_codes_json = '["no_latest_candidates"]'::jsonb))
);

create index if not exists idx_ppssr_generated_at
  on public.paper_project_screening_rank_stability_reports (generated_at desc);

create index if not exists idx_ppssr_status_generated
  on public.paper_project_screening_rank_stability_reports (stability_status, generated_at desc);

create index if not exists idx_ppssr_config_generated
  on public.paper_project_screening_rank_stability_reports (config_version, generated_at desc);

create index if not exists idx_ppssr_reason_codes_json
  on public.paper_project_screening_rank_stability_reports using gin (reason_codes_json);

create index if not exists idx_ppssr_rows_json
  on public.paper_project_screening_rank_stability_reports using gin (rows_json);

create index if not exists idx_ppssr_payload_json
  on public.paper_project_screening_rank_stability_reports using gin (payload_json);
