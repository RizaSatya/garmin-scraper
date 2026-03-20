create table if not exists garmin_auth_tokens (
    account_key text primary key,
    token_payload text not null,
    is_encrypted boolean not null default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
