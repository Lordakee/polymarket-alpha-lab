create table if not exists public.probability_selection_scorer_agreement_trend_gate_reports (
    report_sha256 text primary key,
    generated_at timestamptz not null,
    config_version text not null,
    source_config_version text not null,
    source_generated_at timestamptz not null,
    trend_report_age_seconds integer not null,
    gate_status text not null,
    recommended_next_step text not null,
    reason_code_counts jsonb not null,
    source_report_count integer not null,
    source_trend_status text not null,
    source_recommended_next_step text not null,
    latest_agreement_status text not null,
    latest_agreement_status_streak integer not null,
    aligned_report_count integer not null,
    low_overlap_report_count integer not null,
    gate_blocked_report_count integer not null,
    missing_inputs_report_count integer not null,
    insufficient_identifiers_report_count integer not null,
    average_selected_count numeric not null,
    average_scorer_candidate_count numeric not null,
    latest_source_reason_codes jsonb not null,
    recurring_source_reason_code_counts jsonb not null,
    reason_codes jsonb not null,
    payload jsonb not null,
    paper_only boolean not null default true,
    report_only boolean not null default true,
    readonly boolean not null default true,
    inserted_at timestamptz not null default now(),
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
    check (trend_report_age_seconds >= 0),
    check (gate_status in ('pass', 'watch', 'blocked')),
    check (
        recommended_next_step = case gate_status
            when 'pass' then 'allow_probability_selection_scorer_agreement_trend_review'
            when 'watch' then 'throttle_probability_selection_scorer_agreement_trend_review'
            when 'blocked' then 'block_probability_selection_scorer_agreement_trend_review'
        end
    ),
    check (source_report_count >= 0),
    check (source_trend_status in ('insufficient_history', 'blocked', 'watch', 'stable')),
    check (latest_agreement_status in ('aligned', 'gate_blocked', 'insufficient_identifiers', 'low_overlap', 'missing_inputs')),
    check (latest_agreement_status_streak >= 0),
    check (aligned_report_count >= 0),
    check (low_overlap_report_count >= 0),
    check (gate_blocked_report_count >= 0),
    check (missing_inputs_report_count >= 0),
    check (insufficient_identifiers_report_count >= 0),
    check (average_selected_count >= 0),
    check (average_scorer_candidate_count >= 0),
    check (jsonb_typeof(reason_code_counts) = 'array'),
    check (jsonb_typeof(latest_source_reason_codes) = 'array'),
    check (jsonb_typeof(recurring_source_reason_code_counts) = 'array'),
    check (jsonb_typeof(reason_codes) = 'array'),
    check (jsonb_typeof(payload) = 'object'),
    check (jsonb_array_length(reason_code_counts) >= 1),
    check (jsonb_array_length(reason_codes) >= 1),
    check (paper_only is true),
    check (report_only is true),
    check (readonly is true),
    check (payload ? 'paper_only' and payload -> 'paper_only' = 'true'::jsonb),
    check (payload ? 'report_only' and payload -> 'report_only' = 'true'::jsonb),
    check (payload ? 'readonly' and payload -> 'readonly' = 'true'::jsonb),
    check (payload ? 'generated_at' and jsonb_typeof(payload -> 'generated_at') = 'string' and (payload ->> 'generated_at')::timestamptz = generated_at),
    check (payload ? 'config_version' and jsonb_typeof(payload -> 'config_version') = 'string' and payload ->> 'config_version' = config_version),
    check (payload ? 'source_config_version' and jsonb_typeof(payload -> 'source_config_version') = 'string' and payload ->> 'source_config_version' = source_config_version),
    check (payload ? 'source_generated_at' and jsonb_typeof(payload -> 'source_generated_at') = 'string' and (payload ->> 'source_generated_at')::timestamptz = source_generated_at),
    check (payload ? 'trend_report_age_seconds' and (payload ->> 'trend_report_age_seconds')::integer = trend_report_age_seconds),
    check (payload ? 'trend_report_age_seconds' and payload -> 'trend_report_age_seconds' = to_jsonb(trend_report_age_seconds)),
    check (payload ? 'gate_status' and jsonb_typeof(payload -> 'gate_status') = 'string' and payload ->> 'gate_status' = gate_status),
    check (payload ? 'recommended_next_step' and jsonb_typeof(payload -> 'recommended_next_step') = 'string' and payload ->> 'recommended_next_step' = recommended_next_step),
    check (payload ? 'reason_code_counts' and jsonb_typeof(payload -> 'reason_code_counts') = 'array' and reason_code_counts = payload -> 'reason_code_counts'),
    check (payload ? 'source_report_count' and payload -> 'source_report_count' = to_jsonb(source_report_count)),
    check (payload ? 'source_trend_status' and jsonb_typeof(payload -> 'source_trend_status') = 'string' and payload ->> 'source_trend_status' = source_trend_status),
    check (payload ? 'source_recommended_next_step' and jsonb_typeof(payload -> 'source_recommended_next_step') = 'string' and payload ->> 'source_recommended_next_step' = source_recommended_next_step),
    check (payload ? 'latest_agreement_status' and jsonb_typeof(payload -> 'latest_agreement_status') = 'string' and payload ->> 'latest_agreement_status' = latest_agreement_status),
    check (payload ? 'latest_agreement_status_streak' and payload -> 'latest_agreement_status_streak' = to_jsonb(latest_agreement_status_streak)),
    check (payload ? 'aligned_report_count' and payload -> 'aligned_report_count' = to_jsonb(aligned_report_count)),
    check (payload ? 'low_overlap_report_count' and payload -> 'low_overlap_report_count' = to_jsonb(low_overlap_report_count)),
    check (payload ? 'gate_blocked_report_count' and payload -> 'gate_blocked_report_count' = to_jsonb(gate_blocked_report_count)),
    check (payload ? 'missing_inputs_report_count' and payload -> 'missing_inputs_report_count' = to_jsonb(missing_inputs_report_count)),
    check (payload ? 'insufficient_identifiers_report_count' and payload -> 'insufficient_identifiers_report_count' = to_jsonb(insufficient_identifiers_report_count)),
    check (payload ? 'latest_source_reason_codes' and jsonb_typeof(payload -> 'latest_source_reason_codes') = 'array' and latest_source_reason_codes = payload -> 'latest_source_reason_codes'),
    check (payload ? 'recurring_source_reason_code_counts' and jsonb_typeof(payload -> 'recurring_source_reason_code_counts') = 'array' and recurring_source_reason_code_counts = payload -> 'recurring_source_reason_code_counts'),
    check (payload ? 'reason_codes' and jsonb_typeof(payload -> 'reason_codes') = 'array' and reason_codes = payload -> 'reason_codes'),
    check (payload ? 'average_selected_count' and jsonb_typeof(payload -> 'average_selected_count') = 'string' and (payload ->> 'average_selected_count')::numeric = average_selected_count),
    check (payload ? 'average_scorer_candidate_count' and jsonb_typeof(payload -> 'average_scorer_candidate_count') = 'string' and (payload ->> 'average_scorer_candidate_count')::numeric = average_scorer_candidate_count),
    check (payload ->> 'average_selected_count' ~ '^(0|[1-9][0-9]*)[.][0-9]{6}$'),
    check (payload ->> 'average_scorer_candidate_count' ~ '^(0|[1-9][0-9]*)[.][0-9]{6}$'),
    check (not jsonb_path_exists(reason_code_counts, '$[*] ? (@.paper_only != true || @.report_only != true || @.readonly != true)')),
    check (jsonb_array_length(jsonb_path_query_array(reason_code_counts, '$[*] ? (@.paper_only == true)')) = jsonb_array_length(reason_code_counts)),
    check (jsonb_array_length(jsonb_path_query_array(reason_code_counts, '$[*] ? (@.report_only == true)')) = jsonb_array_length(reason_code_counts)),
    check (jsonb_array_length(jsonb_path_query_array(reason_code_counts, '$[*] ? (@.readonly == true)')) = jsonb_array_length(reason_code_counts)),
    check (not jsonb_path_exists(payload, '$.reason_code_counts[*] ? (@.paper_only != true || @.report_only != true || @.readonly != true)')),
    check (jsonb_array_length(jsonb_path_query_array(payload, '$.reason_code_counts[*] ? (@.paper_only == true)')) = jsonb_array_length(payload -> 'reason_code_counts')),
    check (jsonb_array_length(jsonb_path_query_array(payload, '$.reason_code_counts[*] ? (@.report_only == true)')) = jsonb_array_length(payload -> 'reason_code_counts')),
    check (jsonb_array_length(jsonb_path_query_array(payload, '$.reason_code_counts[*] ? (@.readonly == true)')) = jsonb_array_length(payload -> 'reason_code_counts')),
    check (not (payload ?| array[
        'account',
        'auth',
        'condition_id',
        'market_slug',
        'order',
        'private_key',
        'question',
        'wallet'
    ]))
);

create index if not exists pssatgr_generated_order_idx
    on public.probability_selection_scorer_agreement_trend_gate_reports (generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists pssatgr_config_order_idx
    on public.probability_selection_scorer_agreement_trend_gate_reports (config_version, generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists pssatgr_gate_order_idx
    on public.probability_selection_scorer_agreement_trend_gate_reports (gate_status, generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists pssatgr_source_trend_order_idx
    on public.probability_selection_scorer_agreement_trend_gate_reports (source_trend_status, generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists pssatgr_reason_codes_idx
    on public.probability_selection_scorer_agreement_trend_gate_reports using gin (reason_codes jsonb_path_ops);

create index if not exists pssatgr_payload_idx
    on public.probability_selection_scorer_agreement_trend_gate_reports using gin (payload jsonb_path_ops);
