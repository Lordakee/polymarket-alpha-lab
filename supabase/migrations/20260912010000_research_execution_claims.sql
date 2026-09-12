-- Requires 20260912000000_research_evaluation_capture.sql. Apply once locally.
-- Claims are durable BEFORE model calls; not leases and never automatically reset.
begin;
create table research_capture.execution_claims (
  record_id text primary key check (length(record_id) between 1 and 128 and record_id ~ '^[A-Za-z0-9_.:-]+$'),
  condition_id text not null,
  market_slug text not null,
  team_id text not null,
  model_id text not null,
  protocol_version text not null,
  task_id text not null,
  data_as_of timestamptz not null check (isfinite(data_as_of)),
  claimed_at timestamptz not null,
  request_payload text not null check (octet_length(request_payload) between 1 and 2097152),
  request_sha256 text not null check (request_sha256 ~ '^[a-f0-9]{64}$'),
  paper_only boolean not null default true check (paper_only is true),
  report_only boolean not null default true check (report_only is true),
  readonly boolean not null default true check (readonly is true),
  foreign key (condition_id, market_slug) references research_capture.markets(condition_id, market_slug),
  unique (team_id, model_id, protocol_version, task_id),
  check (data_as_of <= claimed_at),
  check (encode(sha256(convert_to(request_payload, 'UTF8')), 'hex') = request_sha256),
  check ((request_payload::jsonb ->> 'schema_version' = 'research-execution-v1') is true),
  check ((request_payload::jsonb ->> 'record_id' = record_id) is true),
  check ((request_payload::jsonb ->> 'model_id' = model_id) is true),
  check ((request_payload::jsonb ->> 'protocol_version' = protocol_version) is true),
  check ((request_payload::jsonb #>> '{intake,condition_id}' = condition_id) is true),
  check ((request_payload::jsonb #>> '{intake,market_slug}' = market_slug) is true),
  check ((request_payload::jsonb #>> '{intake,team_id}' = team_id) is true),
  check ((request_payload::jsonb #>> '{intake,task_id}' = task_id) is true),
  check (((request_payload::jsonb #>> '{intake,as_of}')::timestamptz = data_as_of) is true),
  check ((request_payload::jsonb -> 'paper_only' = 'true'::jsonb) is true),
  check ((request_payload::jsonb -> 'report_only' = 'true'::jsonb) is true),
  check ((request_payload::jsonb -> 'readonly' = 'true'::jsonb) is true),
  check ((jsonb_typeof(request_payload::jsonb -> 'required_source_ids') = 'array') is true),
  check ((jsonb_array_length(request_payload::jsonb -> 'required_source_ids') <= 20) is true)
);

create function research_capture.stamp_execution_claim() returns trigger
language plpgsql set search_path = pg_catalog as $$
declare cutoff timestamptz; delay_seconds integer;
begin
  perform pg_advisory_xact_lock(hashtextextended('polymarket/research_capture/' || new.condition_id, 0));
  new.claimed_at := clock_timestamp();
  select forecast_cutoff_at into strict cutoff from research_capture.markets
    where condition_id=new.condition_id and market_slug=new.market_slug;
  delay_seconds := (new.request_payload::jsonb ->> 'max_start_delay_seconds')::integer;
  if (delay_seconds between 1 and 3600) is not true
     or ((new.request_payload::jsonb ->> 'forecast_cutoff_at')::timestamptz = cutoff) is not true
     or new.claimed_at >= cutoff or new.data_as_of > new.claimed_at
     or new.claimed_at-new.data_as_of > make_interval(secs => delay_seconds) then
    raise exception 'research_execution_not_startable';
  end if;
  if exists (select 1 from research_capture.attempts a where a.record_id=new.record_id
             or (a.team_id=new.team_id and a.model_id=new.model_id
                 and a.protocol_version=new.protocol_version and a.task_id=new.task_id)) then
    raise exception 'research_execution_identity_used';
  end if;
  if exists (select 1 from research_capture.execution_claims c
             left join research_capture.attempts a on a.record_id=c.record_id
             where c.team_id=new.team_id and c.model_id=new.model_id
               and c.protocol_version=new.protocol_version and c.condition_id=new.condition_id
               and a.record_id is null) then
    raise exception 'research_execution_prior_incomplete';
  end if;
  return new;
end $$;
create trigger stamp_execution_claim before insert on research_capture.execution_claims
  for each row execute function research_capture.stamp_execution_claim();
create trigger immutable_execution_claims before update or delete on research_capture.execution_claims
  for each row execute function research_capture.reject_mutation();
create trigger no_truncate_execution_claims before truncate on research_capture.execution_claims
  for each statement execute function research_capture.reject_mutation();
create index execution_claims_claimed_at_idx on research_capture.execution_claims(claimed_at, record_id);

-- Results captured through the existing API must match any claimed request,
-- even when another application directly uses the old capture API. Unclaimed
-- legacy capture remains supported and unchanged. No probability is rewritten.
create function research_capture.bind_execution_attempt() returns trigger
language plpgsql set search_path = pg_catalog as $$
declare claim research_capture.execution_claims%rowtype;
begin
  perform pg_advisory_xact_lock(hashtextextended('polymarket/research_capture/' || new.condition_id, 0));
  select * into claim from research_capture.execution_claims c where c.record_id=new.record_id
    or (c.team_id=new.team_id and c.model_id=new.model_id
        and c.protocol_version=new.protocol_version and c.task_id=new.task_id);
  if not found then return new; end if;
  if (claim.record_id=new.record_id and claim.condition_id=new.condition_id
      and claim.market_slug=new.market_slug and claim.team_id=new.team_id
      and claim.model_id=new.model_id and claim.protocol_version=new.protocol_version
      and claim.task_id=new.task_id and claim.data_as_of=new.data_as_of
      and claim.claimed_at<=new.recorded_at
      and claim.request_payload::jsonb -> 'intake' = new.payload::jsonb #> '{run,intake}') is not true then
    raise exception 'research_execution_result_mismatch';
  end if;
  if new.payload::jsonb #>> '{run,research,status}' = 'completed' and
     ((new.payload::jsonb #> '{run,research,source_ids}') @>
       (claim.request_payload::jsonb -> 'required_source_ids')) is not true then
    raise exception 'research_execution_required_sources_missing';
  end if;
  return new;
end $$;
-- PostgreSQL orders same-event triggers by name: this must follow stamp_attempt.
create trigger zz_bind_execution_attempt before insert on research_capture.attempts
  for each row execute function research_capture.bind_execution_attempt();
revoke all on research_capture.execution_claims from public;
revoke all on function research_capture.stamp_execution_claim() from public;
revoke all on function research_capture.bind_execution_attempt() from public;
comment on table research_capture.execution_claims is 'Local paper research execution claims; incomplete claims require investigation, never automatic reruns.';
commit;
