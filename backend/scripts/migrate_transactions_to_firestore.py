import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.firebase import firebase_db


COLLECTION = "transactions"
DATA_FILE = Path(__file__).parent.parent / "data" / "transactions.json"


def main() -> None:
    collection = firebase_db.collection(COLLECTION)
    if next(collection.limit(1).stream(), None) is not None:
        print("Firestore transactions collection is not empty; migration skipped.")
        return

    transactions = json.loads(DATA_FILE.read_text())
    now = datetime.now(timezone.utc)
    batch = firebase_db.batch()

    for index, transaction in enumerate(transactions):
        document = collection.document()
        batch.set(
            document,
            {**transaction, "created_at": now - timedelta(seconds=index)},
        )

    batch.commit()
    print(f"Migrated {len(transactions)} transactions to Firestore.")


if __name__ == "__main__":
    main()
