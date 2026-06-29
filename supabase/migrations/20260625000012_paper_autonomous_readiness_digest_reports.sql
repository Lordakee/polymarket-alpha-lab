create table if not exists public.paper_autonomous_readiness_digest_reports (
    report_sha256 text primary key,
    generated_at timestamptz not null,
    config_version text not null,
    digest_status text not null,
    recommended_next_review_action text not null,
    evidence_json jsonb not null,
    source_config_versions_json jsonb not null,
    reason_code_counts_json jsonb not null,
    reason_codes_json jsonb not null,
    payload_json jsonb not null,
    paper_only boolean not null default true,
    report_only boolean not null default true,
    readonly boolean not null default true,
    inserted_at timestamptz not null default now(),
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
    check (digest_status in ('pass', 'watch', 'blocked')),
    check (
        recommended_next_review_action = case digest_status
            when 'pass' then 'continue_operator_review_of_paper_autonomous_readiness_digest'
            when 'watch' then 'review_watch_paper_autonomous_readiness_evidence'
            when 'blocked' then 'review_blocked_paper_autonomous_readiness_evidence'
        end
    ),
    check (jsonb_typeof(evidence_json) = 'array'),
    check (jsonb_typeof(source_config_versions_json) = 'array'),
    check (jsonb_typeof(reason_code_counts_json) = 'array'),
    check (jsonb_typeof(reason_codes_json) = 'array'),
    check (jsonb_typeof(payload_json) = 'object'),
    check (jsonb_array_length(evidence_json) >= 1),
    check (jsonb_array_length(source_config_versions_json) = jsonb_array_length(evidence_json)),
    check (paper_only is true),
    check (report_only is true),
    check (readonly is true),
    check (payload_json ? 'paper_only' and payload_json -> 'paper_only' = 'true'::jsonb),
    check (payload_json ? 'report_only' and payload_json -> 'report_only' = 'true'::jsonb),
    check (payload_json ? 'readonly' and payload_json -> 'readonly' = 'true'::jsonb),
    check (payload_json ? 'generated_at' and jsonb_typeof(payload_json -> 'generated_at') = 'string' and (payload_json ->> 'generated_at')::timestamptz = generated_at),
    check (payload_json ? 'config_version' and jsonb_typeof(payload_json -> 'config_version') = 'string' and payload_json ->> 'config_version' = config_version),
    check (payload_json ? 'digest_status' and jsonb_typeof(payload_json -> 'digest_status') = 'string' and payload_json ->> 'digest_status' = digest_status),
    check (payload_json ? 'recommended_next_review_action' and jsonb_typeof(payload_json -> 'recommended_next_review_action') = 'string' and payload_json ->> 'recommended_next_review_action' = recommended_next_review_action),
    check (payload_json ? 'evidence' and jsonb_typeof(payload_json -> 'evidence') = 'array' and evidence_json = payload_json -> 'evidence'),
    check (payload_json ? 'source_config_versions' and jsonb_typeof(payload_json -> 'source_config_versions') = 'array' and source_config_versions_json = payload_json -> 'source_config_versions'),
    check (payload_json ? 'reason_code_counts' and jsonb_typeof(payload_json -> 'reason_code_counts') = 'array' and reason_code_counts_json = payload_json -> 'reason_code_counts'),
    check (payload_json ? 'reason_codes' and jsonb_typeof(payload_json -> 'reason_codes') = 'array' and reason_codes_json = payload_json -> 'reason_codes')
);

create index if not exists pardr_generated_at_idx
    on public.paper_autonomous_readiness_digest_reports
    (generated_at desc);

create index if not exists pardr_status_generated_idx
    on public.paper_autonomous_readiness_digest_reports
    (digest_status, generated_at desc);

create index if not exists pardr_config_generated_idx
    on public.paper_autonomous_readiness_digest_reports
    (config_version, generated_at desc);

create index if not exists pardr_source_versions_idx
    on public.paper_autonomous_readiness_digest_reports using gin
    (source_config_versions_json jsonb_path_ops);

create index if not exists pardr_reason_codes_idx
    on public.paper_autonomous_readiness_digest_reports using gin
    (reason_codes_json jsonb_path_ops);

create index if not exists pardr_payload_idx
    on public.paper_autonomous_readiness_digest_reports using gin
    (payload_json jsonb_path_ops);

create index if not exists pardr_status_sort_idx
    on public.paper_autonomous_readiness_digest_reports
    (digest_status, generated_at desc, inserted_at desc, report_sha256 desc);
