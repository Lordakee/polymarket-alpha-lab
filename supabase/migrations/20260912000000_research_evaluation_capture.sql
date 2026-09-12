-- Local Supabase/Postgres only. No changes to legacy tables or API schemas.
-- Apply ONCE with the local migration owner; no application auto-migration.
begin;
create schema research_capture;
revoke all on schema research_capture from public;

create function research_capture.reject_mutation() returns trigger
language plpgsql set search_path = pg_catalog as $$
begin
  raise exception 'research_capture_append_only';
end $$;

create table research_capture.markets (
  condition_id text primary key check (length(condition_id) between 1 and 512),
  market_slug text not null check (length(market_slug) <= 200 and market_slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
  forecast_cutoff_at timestamptz not null check (isfinite(forecast_cutoff_at)),
  registered_at timestamptz not null,
  paper_only boolean not null default true check (paper_only is true),
  report_only boolean not null default true check (report_only is true),
  readonly boolean not null default true check (readonly is true),
  unique (condition_id, market_slug),
  check (registered_at < forecast_cutoff_at)
);
create function research_capture.stamp_market() returns trigger
language plpgsql set search_path = pg_catalog as $$
begin
  new.registered_at := clock_timestamp();
  return new;
end $$;
create trigger stamp_market before insert on research_capture.markets
  for each row execute function research_capture.stamp_market();

create table research_capture.attempts (
  record_id text primary key check (length(record_id) between 1 and 128 and record_id ~ '^[A-Za-z0-9_.:-]+$'),
  condition_id text not null,
  market_slug text not null,
  team_id text not null,
  model_id text not null check (length(model_id) between 1 and 128),
  protocol_version text not null check (length(protocol_version) between 1 and 128),
  task_id text not null check (length(task_id) between 1 and 128),
  data_as_of timestamptz not null check (isfinite(data_as_of)),
  recorded_at timestamptz not null,
  payload text not null check (octet_length(payload) between 1 and 2097152),
  payload_sha256 text not null check (payload_sha256 ~ '^[a-f0-9]{64}$'),
  paper_only boolean not null default true check (paper_only is true),
  report_only boolean not null default true check (report_only is true),
  readonly boolean not null default true check (readonly is true),
  foreign key (condition_id, market_slug) references research_capture.markets(condition_id, market_slug),
  unique (team_id, model_id, protocol_version, task_id),
  unique (team_id, model_id, protocol_version, condition_id, recorded_at),
  check (data_as_of <= recorded_at),
  check (encode(sha256(convert_to(payload, 'UTF8')), 'hex') = payload_sha256),
  check ((payload::jsonb ->> 'schema_version' = 'research-capture-v1') is true),
  check ((payload::jsonb ->> 'record_id' = record_id) is true),
  check ((payload::jsonb ->> 'model_id' = model_id) is true),
  check ((payload::jsonb ->> 'protocol_version' = protocol_version) is true),
  check ((payload::jsonb #>> '{run,intake,team_id}' = team_id) is true),
  check ((payload::jsonb #>> '{run,intake,task_id}' = task_id) is true),
  check ((payload::jsonb #>> '{run,intake,condition_id}' = condition_id) is true),
  check ((payload::jsonb #>> '{run,intake,market_slug}' = market_slug) is true),
  check (((payload::jsonb #>> '{run,intake,as_of}')::timestamptz = data_as_of) is true),
  check ((payload::jsonb #> '{run,paper_only}' = 'true'::jsonb) is true),
  check ((payload::jsonb #> '{run,report_only}' = 'true'::jsonb) is true),
  check ((payload::jsonb #> '{run,readonly}' = 'true'::jsonb) is true)
);
create function research_capture.stamp_attempt() returns trigger
language plpgsql set search_path = pg_catalog as $$
begin
  -- Wall clock at insertion, never transaction start or a caller timestamp.
  new.recorded_at := clock_timestamp();
  return new;
end $$;
create trigger stamp_attempt before insert on research_capture.attempts
  for each row execute function research_capture.stamp_attempt();
create index attempts_recorded_at_idx on research_capture.attempts(recorded_at, record_id);

create table research_capture.outcomes (
  condition_id text primary key,
  market_slug text not null,
  forecast_cutoff_at timestamptz not null,
  resolved_at timestamptz not null check (isfinite(resolved_at)),
  recorded_at timestamptz not null,
  actual_yes boolean not null,
  source_reference text not null check (length(source_reference) between 1 and 1024),
  source_content_sha256 text not null check (source_content_sha256 ~ '^[a-f0-9]{64}$'),
  paper_only boolean not null default true check (paper_only is true),
  report_only boolean not null default true check (report_only is true),
  readonly boolean not null default true check (readonly is true),
  foreign key (condition_id, market_slug) references research_capture.markets(condition_id, market_slug),
  check (forecast_cutoff_at <= resolved_at and resolved_at <= recorded_at)
);
create function research_capture.stamp_outcome() returns trigger
language plpgsql set search_path = pg_catalog as $$
begin
  new.recorded_at := clock_timestamp();
  select forecast_cutoff_at into strict new.forecast_cutoff_at
    from research_capture.markets where condition_id = new.condition_id and market_slug = new.market_slug;
  return new;
end $$;
create trigger stamp_outcome before insert on research_capture.outcomes
  for each row execute function research_capture.stamp_outcome();

-- Row triggers prevent update/delete, including owner mistakes. Statement
-- triggers also prevent TRUNCATE. A superuser/owner can still disable them.
create trigger immutable_markets before update or delete on research_capture.markets
  for each row execute function research_capture.reject_mutation();
create trigger immutable_attempts before update or delete on research_capture.attempts
  for each row execute function research_capture.reject_mutation();
create trigger immutable_outcomes before update or delete on research_capture.outcomes
  for each row execute function research_capture.reject_mutation();
create trigger no_truncate_markets before truncate on research_capture.markets
  for each statement execute function research_capture.reject_mutation();
create trigger no_truncate_attempts before truncate on research_capture.attempts
  for each statement execute function research_capture.reject_mutation();
create trigger no_truncate_outcomes before truncate on research_capture.outcomes
  for each statement execute function research_capture.reject_mutation();
revoke all on all tables in schema research_capture from public;
revoke all on all functions in schema research_capture from public;
comment on schema research_capture is 'Local Supabase/Postgres paper research capture; not execution authorization.';
commit;
