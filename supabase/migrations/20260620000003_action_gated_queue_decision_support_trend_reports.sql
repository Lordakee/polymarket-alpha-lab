create table if not exists public.paper_action_gated_queue_decision_support_trend_reports (
    trend_sha256 text primary key,
    trend_schema_version text not null,
    source_window_sha256 text not null,
    generated_at timestamptz not null,
    source_snapshot_count integer not null,
    first_generated_at timestamptz,
    latest_generated_at timestamptz,
    latest_risk_status text,
    risk_pass_count integer not null,
    risk_watch_count integer not null,
    risk_blocked_count integer not null,
    consecutive_latest_watch_count integer not null,
    consecutive_latest_blocked_count integer not null,
    duplicate_generated_at_count integer not null,
    ready_notional_first numeric,
    ready_notional_latest numeric,
    ready_notional_delta numeric,
    top_priority_score_first numeric,
    top_priority_score_latest numeric,
    top_priority_score_delta numeric,
    average_priority_score_first numeric,
    average_priority_score_latest numeric,
    average_priority_score_delta numeric,
    source_queue_count_first integer,
    source_queue_count_latest integer,
    source_queue_count_delta integer,
    latest_reason_code_counts jsonb not null,
    total_reason_code_counts jsonb not null,
    repeated_reason_code_counts jsonb not null,
    reason_code_rows jsonb not null,
    paper_only boolean not null default true,
    report_only boolean not null default true,
    readonly boolean not null default true,
    inserted_at timestamptz not null default now(),
    unique (trend_schema_version, source_window_sha256),
    check (trend_sha256 ~ '^[a-f0-9]{64}$'),
    check (source_window_sha256 ~ '^[a-f0-9]{64}$'),
    check (source_snapshot_count >= 0),
    check (risk_pass_count >= 0),
    check (risk_watch_count >= 0),
    check (risk_blocked_count >= 0),
    check (risk_pass_count + risk_watch_count + risk_blocked_count = source_snapshot_count),
    check (latest_risk_status is null or latest_risk_status in ('pass', 'watch', 'blocked')),
    check (consecutive_latest_watch_count >= 0),
    check (consecutive_latest_watch_count <= source_snapshot_count),
    check (consecutive_latest_blocked_count >= 0),
    check (consecutive_latest_blocked_count <= source_snapshot_count),
    check (duplicate_generated_at_count >= 0),
    check (source_snapshot_count = 0 or duplicate_generated_at_count < source_snapshot_count),
    check (first_generated_at is null or latest_generated_at is null or first_generated_at <= latest_generated_at),
    check (ready_notional_first is null or ready_notional_first >= 0),
    check (ready_notional_latest is null or ready_notional_latest >= 0),
    check (top_priority_score_first is null or top_priority_score_first >= 0),
    check (top_priority_score_latest is null or top_priority_score_latest >= 0),
    check (average_priority_score_first is null or average_priority_score_first >= 0),
    check (average_priority_score_latest is null or average_priority_score_latest >= 0),
    check (source_queue_count_first is null or source_queue_count_first >= 0),
    check (source_queue_count_latest is null or source_queue_count_latest >= 0),
    check (jsonb_typeof(latest_reason_code_counts) = 'object'),
    check (jsonb_typeof(total_reason_code_counts) = 'object'),
    check (jsonb_typeof(repeated_reason_code_counts) = 'object'),
    check (jsonb_typeof(reason_code_rows) = 'array'),
    check ((source_snapshot_count = 0
            and first_generated_at is null
            and latest_generated_at is null
            and latest_risk_status is null
            and ready_notional_first is null
            and ready_notional_latest is null
            and ready_notional_delta is null
            and top_priority_score_first is null
            and top_priority_score_latest is null
            and top_priority_score_delta is null
            and average_priority_score_first is null
            and average_priority_score_latest is null
            and average_priority_score_delta is null
            and source_queue_count_first is null
            and source_queue_count_latest is null
            and source_queue_count_delta is null
        )
        or (source_snapshot_count > 0
            and first_generated_at is not null
            and latest_generated_at is not null
            and latest_risk_status is not null
            and ready_notional_first is not null
            and ready_notional_latest is not null
            and ready_notional_delta is not null
            and top_priority_score_first is not null
            and top_priority_score_latest is not null
            and top_priority_score_delta is not null
            and average_priority_score_first is not null
            and average_priority_score_latest is not null
            and average_priority_score_delta is not null
            and source_queue_count_first is not null
            and source_queue_count_latest is not null
            and source_queue_count_delta is not null
        )),
    check (paper_only is true),
    check (report_only is true),
    check (readonly is true)
);

create table if not exists public.paper_action_gated_queue_decision_support_trend_sources (
    trend_sha256 text not null,
    trend_ordinal integer not null,
    source_input_position integer not null,
    snapshot_sha256 text not null,
    source_generated_at timestamptz not null,
    paper_only boolean not null default true,
    report_only boolean not null default true,
    readonly boolean not null default true,
    inserted_at timestamptz not null default now(),
    primary key (trend_sha256, trend_ordinal),
    unique (trend_sha256, source_input_position),
    foreign key (trend_sha256) references public.paper_action_gated_queue_decision_support_trend_reports(trend_sha256) on delete cascade,
    foreign key (snapshot_sha256) references public.paper_action_gated_strategy_recommendation_queue_decision_support_reports(snapshot_sha256),
    check (trend_sha256 ~ '^[a-f0-9]{64}$'),
    check (snapshot_sha256 ~ '^[a-f0-9]{64}$'),
    check (trend_ordinal >= 1),
    check (source_input_position >= 1),
    check (paper_only is true),
    check (report_only is true),
    check (readonly is true)
);

create index if not exists idx_pagqdst_generated_at
    on public.paper_action_gated_queue_decision_support_trend_reports (generated_at desc);

create index if not exists idx_pagqdst_risk_generated
    on public.paper_action_gated_queue_decision_support_trend_reports (latest_risk_status, generated_at desc);

create index if not exists idx_pagqdst_inserted
    on public.paper_action_gated_queue_decision_support_trend_reports (generated_at desc, inserted_at desc, trend_sha256 desc);

create index if not exists idx_pagqdst_src_snapshot
    on public.paper_action_gated_queue_decision_support_trend_sources (snapshot_sha256);

create index if not exists idx_pagqdst_src_generated
    on public.paper_action_gated_queue_decision_support_trend_sources (source_generated_at desc);
