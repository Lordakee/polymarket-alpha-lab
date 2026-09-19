-- Explicit uncapped authorization and observed call metadata, NOT billing.
create table research_capture.uncapped_authorizations (
  authorization_id text primary key check (authorization_id ~ '^[A-Za-z0-9_.:-]{1,128}$'),
  payload text not null check (octet_length(payload) between 1 and 32768),
  payload_sha256 text not null check (payload_sha256 ~ '^[a-f0-9]{64}$'),
  recorded_at timestamptz not null check (isfinite(recorded_at)),
  paper_only boolean not null default true check (paper_only is true),
  report_only boolean not null default true check (report_only is true),
  readonly boolean not null default true check (readonly is true),
  check (encode(sha256(convert_to(payload,'UTF8')),'hex') = payload_sha256)
);

create function research_capture.stamp_uncapped_authorization() returns trigger
language plpgsql set search_path = pg_catalog as $$
declare body jsonb; approved timestamptz; expiry timestamptz; item jsonb; ids text[] := '{}';
begin
  perform pg_advisory_xact_lock(hashtextextended('polymarket/uncapped_audit/authorization/' || new.authorization_id,0));
  new.recorded_at := clock_timestamp();
  body := new.payload::jsonb;
  approved := (body ->> 'approved_at')::timestamptz;
  expiry := (body ->> 'expires_at')::timestamptz;
  if (jsonb_typeof(body) = 'object'
      and body - array['schema_version','authorization_id','model_id','adapter_contract_sha256',
          'approved_at','expires_at','request_keys','no_monetary_cap_approved',
          'research_data_send_approved','paper_only','report_only','readonly'] = '{}'::jsonb
      and body ->> 'schema_version' = 'research-no-monetary-cap-v1'
      and body ->> 'authorization_id' = new.authorization_id
      and jsonb_typeof(body -> 'model_id') = 'string'
      and length(body ->> 'model_id') between 1 and 128
      and btrim(body ->> 'model_id') = body ->> 'model_id'
      and body ->> 'adapter_contract_sha256' ~ '^[a-f0-9]{64}$'
      and isfinite(approved) and isfinite(expiry)
      and approved <= new.recorded_at and new.recorded_at < expiry
      and body -> 'no_monetary_cap_approved' = 'true'::jsonb
      and body -> 'research_data_send_approved' = 'true'::jsonb
      and body -> 'paper_only' = 'true'::jsonb
      and body -> 'report_only' = 'true'::jsonb
      and body -> 'readonly' = 'true'::jsonb
      and jsonb_typeof(body -> 'request_keys') = 'array'
      and jsonb_array_length(body -> 'request_keys') between 1 and 100) is not true then
    raise exception 'research_uncapped_audit_authorization_invalid';
  end if;
  for item in select value from jsonb_array_elements(body -> 'request_keys') loop
    if (jsonb_typeof(item) = 'array' and jsonb_array_length(item) = 2
        and jsonb_typeof(item -> 0) = 'string' and jsonb_typeof(item -> 1) = 'string'
        and item ->> 0 ~ '^[A-Za-z0-9_.:-]{1,128}$'
        and item ->> 1 ~ '^[a-f0-9]{64}$') is not true or item ->> 0 = any(ids) then
      raise exception 'research_uncapped_audit_roster_invalid';
    end if;
    ids := array_append(ids,item ->> 0);
  end loop;
  return new;
end $$;
create trigger stamp_uncapped_authorization before insert on research_capture.uncapped_authorizations
  for each row execute function research_capture.stamp_uncapped_authorization();

create table research_capture.uncapped_call_starts (
  authorization_id text not null references research_capture.uncapped_authorizations(authorization_id),
  authorization_sha256 text not null check (authorization_sha256 ~ '^[a-f0-9]{64}$'),
  record_id text not null references research_capture.execution_claims(record_id),
  request_sha256 text not null check (request_sha256 ~ '^[a-f0-9]{64}$'),
  call_number integer not null check (call_number between 1 and 32),
  message_sha256 text not null check (message_sha256 ~ '^[a-f0-9]{64}$'),
  message_bytes integer not null check (message_bytes between 1 and 2000000),
  max_output_tokens integer not null check (max_output_tokens between 1 and 8192),
  started_at timestamptz not null check (isfinite(started_at)),
  paper_only boolean not null default true check (paper_only is true),
  report_only boolean not null default true check (report_only is true),
  readonly boolean not null default true check (readonly is true),
  primary key (record_id,call_number)
);

create table research_capture.uncapped_call_outcomes (
  record_id text not null,
  call_number integer not null,
  status text not null check (status in ('returned','failed','interrupted')),
  reported_total_tokens integer,
  reply_sha256 text,
  recorded_at timestamptz not null check (isfinite(recorded_at)),
  paper_only boolean not null default true check (paper_only is true),
  report_only boolean not null default true check (report_only is true),
  readonly boolean not null default true check (readonly is true),
  primary key (record_id,call_number),
  foreign key (record_id,call_number) references research_capture.uncapped_call_starts(record_id,call_number),
  check ((status='returned' and reported_total_tokens is not null
          and reported_total_tokens between 1 and 1000000 and reply_sha256 is not null
          and reply_sha256 ~ '^[a-f0-9]{64}$')
      or (status in ('failed','interrupted') and reported_total_tokens is null and reply_sha256 is null))
);

create function research_capture.stamp_uncapped_call() returns trigger
language plpgsql set search_path = pg_catalog as $$
declare policy research_capture.uncapped_authorizations%rowtype;
        claimed research_capture.execution_claims%rowtype;
        previous research_capture.uncapped_call_starts%rowtype;
        terminal research_capture.uncapped_call_outcomes%rowtype;
        body jsonb; last_call integer;
begin
  perform pg_advisory_xact_lock(hashtextextended('polymarket/uncapped_audit/call/' || new.record_id,0));
  select * into policy from research_capture.uncapped_authorizations where authorization_id=new.authorization_id;
  select * into claimed from research_capture.execution_claims where record_id=new.record_id;
  new.started_at := clock_timestamp();
  body := policy.payload::jsonb;
  if (policy.payload_sha256 = new.authorization_sha256
      and claimed.request_sha256 = new.request_sha256
      and claimed.model_id = body ->> 'model_id'
      and claimed.team_id in ('crypto_btc','crypto_eth')
      and new.started_at >= claimed.claimed_at and new.started_at >= policy.recorded_at
      and new.started_at >= (body ->> 'approved_at')::timestamptz
      and new.started_at < (body ->> 'expires_at')::timestamptz
      and new.started_at < (claimed.request_payload::jsonb ->> 'forecast_cutoff_at')::timestamptz
      and new.max_output_tokens <= (claimed.request_payload::jsonb #>> '{limits,max_output_tokens}')::integer
      and new.call_number <= (claimed.request_payload::jsonb #>> '{limits,max_model_calls}')::integer) is not true
      or not exists (select 1 from jsonb_array_elements(body -> 'request_keys') k(value)
        where k.value ->> 0 = new.record_id and k.value ->> 1 = new.request_sha256)
      or exists (select 1 from research_capture.attempts where record_id=new.record_id)
      or exists (select 1 from research_capture.model_call_reservations where record_id=new.record_id) then
    raise exception 'research_uncapped_audit_call_not_allowed';
  end if;
  select coalesce(max(call_number),0) into last_call from research_capture.uncapped_call_starts
    where record_id=new.record_id;
  if new.call_number <> last_call+1 then
    raise exception 'research_uncapped_audit_call_sequence';
  end if;
  if last_call > 0 then
    select * into previous from research_capture.uncapped_call_starts
      where record_id=new.record_id and call_number=last_call;
    select * into terminal from research_capture.uncapped_call_outcomes
      where record_id=new.record_id and call_number=last_call;
    if (previous.authorization_id=new.authorization_id
        and previous.authorization_sha256=new.authorization_sha256
        and terminal.status='returned' and new.started_at >= terminal.recorded_at) is not true then
      raise exception 'research_uncapped_audit_previous_call_unresolved';
    end if;
  end if;
  return new;
end $$;
create trigger stamp_uncapped_call before insert on research_capture.uncapped_call_starts
  for each row execute function research_capture.stamp_uncapped_call();

create function research_capture.stamp_uncapped_outcome() returns trigger
language plpgsql set search_path = pg_catalog as $$
declare started timestamptz;
begin
  perform pg_advisory_xact_lock(hashtextextended('polymarket/uncapped_audit/call/' || new.record_id,0));
  select started_at into started from research_capture.uncapped_call_starts
    where record_id=new.record_id and call_number=new.call_number;
  new.recorded_at := clock_timestamp();
  if (new.recorded_at >= started) is not true then
    raise exception 'research_uncapped_audit_outcome_not_allowed';
  end if;
  return new;
end $$;
create trigger stamp_uncapped_outcome before insert on research_capture.uncapped_call_outcomes
  for each row execute function research_capture.stamp_uncapped_outcome();

create trigger immutable_uncapped_authorizations before update or delete on research_capture.uncapped_authorizations
  for each row execute function research_capture.reject_mutation();
create trigger no_truncate_uncapped_authorizations before truncate on research_capture.uncapped_authorizations
  for each statement execute function research_capture.reject_mutation();
create trigger immutable_uncapped_call_starts before update or delete on research_capture.uncapped_call_starts
  for each row execute function research_capture.reject_mutation();
create trigger no_truncate_uncapped_call_starts before truncate on research_capture.uncapped_call_starts
  for each statement execute function research_capture.reject_mutation();
create trigger immutable_uncapped_call_outcomes before update or delete on research_capture.uncapped_call_outcomes
  for each row execute function research_capture.reject_mutation();
create trigger no_truncate_uncapped_call_outcomes before truncate on research_capture.uncapped_call_outcomes
  for each statement execute function research_capture.reject_mutation();
revoke all on research_capture.uncapped_authorizations,research_capture.uncapped_call_starts,
  research_capture.uncapped_call_outcomes from public;
revoke all on function research_capture.stamp_uncapped_authorization(),research_capture.stamp_uncapped_call(),
  research_capture.stamp_uncapped_outcome() from public;
comment on table research_capture.uncapped_call_starts is
  'Committed before application client entry; not proof of provider submission. Missing outcome means unknown.';
comment on table research_capture.uncapped_call_outcomes is
  'Application-observed outcome and reported usage, not an invoice, refund or provider identity certificate.';
