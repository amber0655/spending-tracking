import pytest

from app.firebase import FIREBASE_ENV_FIELDS, service_account_from_environment


def clear_firebase_environment(monkeypatch) -> None:
    for environment_name in FIREBASE_ENV_FIELDS.values():
        monkeypatch.delenv(environment_name, raising=False)


def test_service_account_from_environment_converts_private_key_newlines(
    monkeypatch,
) -> None:
    clear_firebase_environment(monkeypatch)
    values = {
        "FIREBASE_PROJECT_ID": "spending-tracker",
        "FIREBASE_PRIVATE_KEY_ID": "private-key-id",
        "FIREBASE_PRIVATE_KEY": "-----BEGIN PRIVATE KEY-----\\nkey\\n-----END PRIVATE KEY-----\\n",
        "FIREBASE_CLIENT_EMAIL": "firebase@example.iam.gserviceaccount.com",
        "FIREBASE_CLIENT_ID": "client-id",
        "FIREBASE_CLIENT_X509_CERT_URL": "https://example.com/certificate",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)

    service_account = service_account_from_environment()

    assert service_account is not None
    assert service_account["project_id"] == "spending-tracker"
    assert service_account["private_key"] == (
        "-----BEGIN PRIVATE KEY-----\nkey\n-----END PRIVATE KEY-----\n"
    )
    assert service_account["token_uri"] == "https://oauth2.googleapis.com/token"


def test_service_account_from_environment_rejects_partial_configuration(
    monkeypatch,
) -> None:
    clear_firebase_environment(monkeypatch)
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "spending-tracker")

    with pytest.raises(RuntimeError, match="FIREBASE_PRIVATE_KEY"):
        service_account_from_environment()
