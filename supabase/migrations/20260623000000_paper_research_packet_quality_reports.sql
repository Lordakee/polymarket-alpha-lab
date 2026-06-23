create table if not exists public.paper_research_packet_quality_reports (
  report_sha256 text primary key
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
  generated_at timestamptz not null,
  config_version text not null,
  source_generated_at timestamptz not null,
  source_config_version text not null,
  input_row_count integer not null
    check (input_row_count >= 0),
  packet_row_count integer not null
    check (packet_row_count >= 0),
  included_count integer not null
    check (included_count >= 0),
  skipped_count integer not null
    check (skipped_count >= 0),
  high_priority_count integer not null
    check (high_priority_count >= 0),
  medium_priority_count integer not null
    check (medium_priority_count >= 0),
  low_priority_count integer not null
    check (low_priority_count >= 0),
  source_age_seconds integer not null
    check (source_age_seconds >= 0),
  included_share numeric(18, 6) null
    check (included_share is null or (included_share >= 0 and included_share <= 1)),
  skipped_share numeric(18, 6) null
    check (skipped_share is null or (skipped_share >= 0 and skipped_share <= 1)),
  check_count integer not null
    check (check_count >= 0),
  pass_count integer not null
    check (pass_count >= 0),
  watch_count integer not null
    check (watch_count >= 0),
  blocked_count integer not null
    check (blocked_count >= 0),
  quality_status text not null
    check (quality_status in ('pass', 'watch', 'blocked')),
  check_rows_json jsonb not null default '[]'::jsonb
    check (jsonb_typeof(check_rows_json) = 'array'),
  reason_code_counts_json jsonb not null default '[]'::jsonb
    check (jsonb_typeof(reason_code_counts_json) = 'array'),
  reason_codes_json jsonb not null default '[]'::jsonb
    check (jsonb_typeof(reason_codes_json) = 'array'),
  reason_code_count integer not null
    check (reason_code_count >= 0),
  payload_json jsonb not null
    check (jsonb_typeof(payload_json) = 'object'),
  paper_only boolean not null default true
    check (paper_only is true),
  report_only boolean not null default true
    check (report_only is true),
  readonly boolean not null default true
    check (readonly is true),
  inserted_at timestamptz not null default now(),
  check (source_generated_at <= generated_at),
  check (input_row_count >= packet_row_count),
  check (packet_row_count = included_count + skipped_count),
  check (included_count = high_priority_count + medium_priority_count + low_priority_count),
  check (check_count = 3),
  check (check_count = pass_count + watch_count + blocked_count),
  check (check_count = jsonb_array_length(check_rows_json)),
  check (reason_code_count = jsonb_array_length(reason_codes_json)),
  check (reason_code_count = jsonb_array_length(reason_code_counts_json)),
  check ((check_rows_json -> 0 ->> 'check_name') = 'source_freshness'),
  check ((check_rows_json -> 1 ->> 'check_name') = 'packet_population'),
  check ((check_rows_json -> 2 ->> 'check_name') = 'skip_pressure'),
  check (
    pass_count = jsonb_array_length(
      jsonb_path_query_array(check_rows_json, '$[*] ? (@.status == "pass")')
    )
  ),
  check (
    watch_count = jsonb_array_length(
      jsonb_path_query_array(check_rows_json, '$[*] ? (@.status == "watch")')
    )
  ),
  check (
    blocked_count = jsonb_array_length(
      jsonb_path_query_array(check_rows_json, '$[*] ? (@.status == "blocked")')
    )
  ),
  check (
    (
      quality_status = 'blocked'
      and blocked_count > 0
    )
    or (
      quality_status = 'watch'
      and blocked_count = 0
      and watch_count > 0
    )
    or (
      quality_status = 'pass'
      and blocked_count = 0
      and watch_count = 0
    )
  ),
  check (((payload_json -> 'paper_only') = 'true'::jsonb) is true),
  check (((payload_json -> 'report_only') = 'true'::jsonb) is true),
  check (((payload_json -> 'readonly') = 'true'::jsonb) is true),
  check (
    payload_json ? 'generated_at'
    and jsonb_typeof(payload_json -> 'generated_at') = 'string'
    and (payload_json ->> 'generated_at')::timestamptz = generated_at
  ),
  check (
    payload_json ? 'config_version'
    and jsonb_typeof(payload_json -> 'config_version') = 'string'
    and payload_json ->> 'config_version' = config_version
  ),
  check (
    payload_json ? 'source_generated_at'
    and jsonb_typeof(payload_json -> 'source_generated_at') = 'string'
    and (payload_json ->> 'source_generated_at')::timestamptz = source_generated_at
  ),
  check (
    payload_json ? 'source_config_version'
    and jsonb_typeof(payload_json -> 'source_config_version') = 'string'
    and payload_json ->> 'source_config_version' = source_config_version
  ),
  check (((payload_json -> 'input_row_count') = to_jsonb(input_row_count)) is true),
  check (((payload_json -> 'packet_row_count') = to_jsonb(packet_row_count)) is true),
  check (((payload_json -> 'included_count') = to_jsonb(included_count)) is true),
  check (((payload_json -> 'skipped_count') = to_jsonb(skipped_count)) is true),
  check (((payload_json -> 'high_priority_count') = to_jsonb(high_priority_count)) is true),
  check (((payload_json -> 'medium_priority_count') = to_jsonb(medium_priority_count)) is true),
  check (((payload_json -> 'low_priority_count') = to_jsonb(low_priority_count)) is true),
  check (((payload_json -> 'source_age_seconds') = to_jsonb(source_age_seconds)) is true),
  check (
    (
      included_share is null
      and ((payload_json -> 'included_share') = 'null'::jsonb) is true
    )
    or (
      included_share is not null
      and jsonb_typeof(payload_json -> 'included_share') = 'string'
      and (payload_json ->> 'included_share')::numeric(18, 6) = included_share
    )
  ),
  check (
    (
      skipped_share is null
      and ((payload_json -> 'skipped_share') = 'null'::jsonb) is true
    )
    or (
      skipped_share is not null
      and jsonb_typeof(payload_json -> 'skipped_share') = 'string'
      and (payload_json ->> 'skipped_share')::numeric(18, 6) = skipped_share
    )
  ),
  check (((payload_json -> 'check_count') = to_jsonb(check_count)) is true),
  check (((payload_json -> 'pass_count') = to_jsonb(pass_count)) is true),
  check (((payload_json -> 'watch_count') = to_jsonb(watch_count)) is true),
  check (((payload_json -> 'blocked_count') = to_jsonb(blocked_count)) is true),
  check (
    payload_json ? 'quality_status'
    and jsonb_typeof(payload_json -> 'quality_status') = 'string'
    and payload_json ->> 'quality_status' = quality_status
  ),
  check (((payload_json -> 'check_rows') = check_rows_json) is true),
  check (((payload_json -> 'reason_code_counts') = reason_code_counts_json) is true),
  check (reason_codes_json = jsonb_path_query_array(reason_code_counts_json, '$[*].reason_code')),
  check (
    jsonb_array_length(
      jsonb_path_query_array(check_rows_json, '$[*] ? (@.paper_only == true)')
    ) = check_count
  ),
  check (
    jsonb_array_length(
      jsonb_path_query_array(check_rows_json, '$[*] ? (@.report_only == true)')
    ) = check_count
  ),
  check (
    jsonb_array_length(
      jsonb_path_query_array(check_rows_json, '$[*] ? (@.readonly == true)')
    ) = check_count
  ),
  check (
    jsonb_array_length(
      jsonb_path_query_array(reason_code_counts_json, '$[*] ? (@.paper_only == true)')
    ) = reason_code_count
  ),
  check (
    jsonb_array_length(
      jsonb_path_query_array(reason_code_counts_json, '$[*] ? (@.report_only == true)')
    ) = reason_code_count
  ),
  check (
    jsonb_array_length(
      jsonb_path_query_array(reason_code_counts_json, '$[*] ? (@.readonly == true)')
    ) = reason_code_count
  ),
  check (
    jsonb_array_length(
      jsonb_path_query_array(payload_json, '$.check_rows[*] ? (@.paper_only == true)')
    ) = check_count
  ),
  check (
    jsonb_array_length(
      jsonb_path_query_array(payload_json, '$.check_rows[*] ? (@.report_only == true)')
    ) = check_count
  ),
  check (
    jsonb_array_length(
      jsonb_path_query_array(payload_json, '$.check_rows[*] ? (@.readonly == true)')
    ) = check_count
  ),
  check (
    jsonb_array_length(
      jsonb_path_query_array(payload_json, '$.reason_code_counts[*] ? (@.paper_only == true)')
    ) = reason_code_count
  ),
  check (
    jsonb_array_length(
      jsonb_path_query_array(payload_json, '$.reason_code_counts[*] ? (@.report_only == true)')
    ) = reason_code_count
  ),
  check (
    jsonb_array_length(
      jsonb_path_query_array(payload_json, '$.reason_code_counts[*] ? (@.readonly == true)')
    ) = reason_code_count
  ),
  check (
    not jsonb_path_exists(
      check_rows_json,
      '$[*] ? (@.paper_only != true || @.report_only != true || @.readonly != true)'
    )
  ),
  check (
    not jsonb_path_exists(
      reason_code_counts_json,
      '$[*] ? (@.paper_only != true || @.report_only != true || @.readonly != true)'
    )
  ),
  check (
    not jsonb_path_exists(
      payload_json,
      '$.check_rows[*] ? (@.paper_only != true || @.report_only != true || @.readonly != true)'
    )
  ),
  check (
    not jsonb_path_exists(
      payload_json,
      '$.reason_code_counts[*] ? (@.paper_only != true || @.report_only != true || @.readonly != true)'
    )
  )
);

create index if not exists idx_prpqr_generated_at
  on public.paper_research_packet_quality_reports (generated_at desc);

create index if not exists idx_prpqr_config_version_generated_at
  on public.paper_research_packet_quality_reports (config_version, generated_at desc);

create index if not exists idx_prpqr_quality_status_generated_at
  on public.paper_research_packet_quality_reports (quality_status, generated_at desc);

create index if not exists idx_prpqr_source_generated_at
  on public.paper_research_packet_quality_reports (source_generated_at desc);

create index if not exists idx_prpqr_check_rows_json
  on public.paper_research_packet_quality_reports using gin (check_rows_json jsonb_path_ops);

create index if not exists idx_prpqr_reason_codes_json
  on public.paper_research_packet_quality_reports using gin (reason_codes_json jsonb_path_ops);

create index if not exists idx_prpqr_payload_json
  on public.paper_research_packet_quality_reports using gin (payload_json jsonb_path_ops);
