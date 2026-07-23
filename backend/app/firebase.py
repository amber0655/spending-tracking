import os
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.firestore import Client


DEFAULT_CREDENTIAL_PATH = (
    Path(__file__).parent.parent
    / "spending-tracker-9c3a7-firebase-adminsdk-fbsvc-ba67f1539e.json"
)

FIREBASE_ENV_FIELDS = {
    "type": "FIREBASE_TYPE",
    "project_id": "FIREBASE_PROJECT_ID",
    "private_key_id": "FIREBASE_PRIVATE_KEY_ID",
    "private_key": "FIREBASE_PRIVATE_KEY",
    "client_email": "FIREBASE_CLIENT_EMAIL",
    "client_id": "FIREBASE_CLIENT_ID",
    "auth_uri": "FIREBASE_AUTH_URI",
    "token_uri": "FIREBASE_TOKEN_URI",
    "auth_provider_x509_cert_url": "FIREBASE_AUTH_PROVIDER_X509_CERT_URL",
    "client_x509_cert_url": "FIREBASE_CLIENT_X509_CERT_URL",
    "universe_domain": "FIREBASE_UNIVERSE_DOMAIN",
}

FIREBASE_ENV_DEFAULTS = {
    "type": "service_account",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "universe_domain": "googleapis.com",
}

FIREBASE_REQUIRED_ENV_FIELDS = {
    "project_id",
    "private_key_id",
    "private_key",
    "client_email",
    "client_id",
    "client_x509_cert_url",
}


def service_account_from_environment() -> dict[str, str] | None:
    configured_values = {
        field: os.environ.get(environment_name)
        for field, environment_name in FIREBASE_ENV_FIELDS.items()
    }

    if not any(configured_values.values()):
        return None

    missing_fields = sorted(
        FIREBASE_ENV_FIELDS[field]
        for field in FIREBASE_REQUIRED_ENV_FIELDS
        if not configured_values[field]
    )
    if missing_fields:
        raise RuntimeError(
            "Firebase environment configuration is incomplete. Missing: "
            + ", ".join(missing_fields)
        )

    service_account = {
        field: configured_values[field] or default
        for field, default in FIREBASE_ENV_DEFAULTS.items()
    }
    service_account.update(
        {
            field: value
            for field, value in configured_values.items()
            if value is not None
        }
    )
    service_account["private_key"] = service_account["private_key"].replace(
        "\\n", "\n"
    )
    return service_account


def initialize_firebase() -> tuple[firebase_admin.App, Client]:
    try:
        firebase_app = firebase_admin.get_app()
    except ValueError:
        service_account = service_account_from_environment()
        if service_account is not None:
            credential = credentials.Certificate(service_account)
        else:
            credential_path = Path(
                os.environ.get("FIREBASE_SERVICE_ACCOUNT", DEFAULT_CREDENTIAL_PATH)
            ).expanduser()

            if not credential_path.is_file():
                raise RuntimeError(
                    "Firebase credentials not found. Configure the FIREBASE_* "
                    "environment variables or set FIREBASE_SERVICE_ACCOUNT."
                )

            credential = credentials.Certificate(str(credential_path))

        firebase_app = firebase_admin.initialize_app(credential)

    return firebase_app, firestore.client(app=firebase_app)


firebase_app, firebase_db = initialize_firebase()
