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
