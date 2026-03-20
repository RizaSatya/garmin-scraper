from cryptography.fernet import Fernet

from garmin_sync.crypto import decrypt_token, encrypt_token


def test_encrypt_and_decrypt_round_trip():
    key = Fernet.generate_key().decode()
    plaintext = "serialized-token-payload"

    ciphertext = encrypt_token(plaintext, key)

    assert ciphertext != plaintext
    assert decrypt_token(ciphertext, key) == plaintext
