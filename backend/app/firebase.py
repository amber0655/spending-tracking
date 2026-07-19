import os
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.firestore import Client


DEFAULT_CREDENTIAL_PATH = (
    Path(__file__).parent.parent
    / "spending-tracker-9c3a7-firebase-adminsdk-fbsvc-ba67f1539e.json"
)


def initialize_firebase() -> tuple[firebase_admin.App, Client]:
    try:
        firebase_app = firebase_admin.get_app()
    except ValueError:
        credential_path = Path(
            os.environ.get("FIREBASE_SERVICE_ACCOUNT", DEFAULT_CREDENTIAL_PATH)
        ).expanduser()

        if not credential_path.is_file():
            raise RuntimeError(
                "Firebase service-account file not found. Set "
                "FIREBASE_SERVICE_ACCOUNT to its path."
            )

        credential = credentials.Certificate(str(credential_path))
        firebase_app = firebase_admin.initialize_app(credential)

    return firebase_app, firestore.client(app=firebase_app)


firebase_app, firebase_db = initialize_firebase()
