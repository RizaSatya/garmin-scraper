from dataclasses import dataclass

from garmin_sync.crypto import decrypt_token, encrypt_token


@dataclass(frozen=True)
class TokenRecord:
    account_key: str
    token_payload: str
    is_encrypted: bool


def serialize_token_record(
    account_key: str,
    token_payload: str,
    fernet_key: str | None,
) -> TokenRecord:
    if fernet_key:
        return TokenRecord(
            account_key=account_key,
            token_payload=encrypt_token(token_payload, fernet_key),
            is_encrypted=True,
        )
    return TokenRecord(
        account_key=account_key,
        token_payload=token_payload,
        is_encrypted=False,
    )


def deserialize_token_payload(
    token_payload: str,
    is_encrypted: bool,
    fernet_key: str | None,
) -> str:
    if is_encrypted:
        if not fernet_key:
            raise ValueError("FERNET_KEY is required to decrypt stored Garmin tokens")
        return decrypt_token(token_payload, fernet_key)
    return token_payload


def load_token_payload(conn, account_key: str, fernet_key: str | None) -> str | None:
    row = conn.execute(
        """
        select token_payload, is_encrypted
        from garmin_auth_tokens
        where account_key = %s
        """,
        (account_key,),
    ).fetchone()
    if row is None:
        return None
    return deserialize_token_payload(row[0], row[1], fernet_key)


def save_token_payload(
    conn,
    account_key: str,
    token_payload: str,
    fernet_key: str | None,
) -> None:
    record = serialize_token_record(account_key, token_payload, fernet_key)
    conn.execute(
        """
        insert into garmin_auth_tokens (account_key, token_payload, is_encrypted, created_at, updated_at)
        values (%s, %s, %s, now(), now())
        on conflict (account_key)
        do update set
            token_payload = excluded.token_payload,
            is_encrypted = excluded.is_encrypted,
            updated_at = now()
        """,
        (record.account_key, record.token_payload, record.is_encrypted),
    )
