import pytest
from datetime import date
from fastapi.testclient import TestClient

from app import main
from app.main import INITIAL_TRANSACTIONS, Transaction, app, period_start


client = TestClient(app)
TEST_USER_ID = "test-user-123"


@pytest.fixture(autouse=True)
def fake_firestore(monkeypatch) -> dict[str, list[Transaction]]:
    records = {TEST_USER_ID: [item.model_copy() for item in INITIAL_TRANSACTIONS]}
    app.dependency_overrides[main.get_current_user_id] = lambda: TEST_USER_ID
    monkeypatch.setattr(
        main,
        "list_transactions",
        lambda user_id, period="this_month": records.get(user_id, []),
    )
    monkeypatch.setattr(
        main,
        "save_transaction",
        lambda user_id, item: records.setdefault(user_id, []).insert(0, item),
    )
    async def fake_receipt_parser(_image: bytes, _mime_type: str) -> Transaction:
        return Transaction(
            icon="bag",
            merchant="Aura Market",
            meta="Shopping • Receipt",
            amount="- $34.25",
            kind="Expense",
            income=False,
            date=date(2026, 7, 21),
        )

    monkeypatch.setattr(main, "parse_receipt_with_gemini", fake_receipt_parser)
    yield records
    app.dependency_overrides.clear()


def test_get_transactions_returns_page_data() -> None:
    response = client.get("/transactions")

    assert response.status_code == 200
    assert len(response.json()) == 6
    assert response.json()[0] == {
        "icon": "coffee",
        "merchant": "Sweetgreen",
        "meta": "Food & Dining • Credit",
        "amount": "- $18.45",
        "kind": "Expense",
    }


def test_create_transaction() -> None:
    payload = {
        "icon": "card",
        "merchant": "Cloud Storage",
        "meta": "Subscriptions • Credit",
        "amount": "- $9.99",
        "kind": "Expense",
    }

    create_response = client.post("/transactions", json=payload)
    assert create_response.status_code == 201
    assert create_response.json() == payload
    assert client.get("/transactions").json()[0] == payload


def test_period_start_dates() -> None:
    today = date(2026, 7, 19)

    assert period_start("this_week", today) == date(2026, 7, 13)
    assert period_start("this_month", today) == date(2026, 7, 1)
    assert period_start("last_3_months", today) == date(2026, 5, 1)


def test_put_transaction() -> None:
    payload = {
        "icon": "dots",
        "merchant": "Dinner with colleagues",
        "meta": "Other • 2026-07-19",
        "amount": "- $28.50",
        "kind": "Expense",
        "income": False,
    }

    response = client.put("/transactions", json=payload)

    assert response.status_code == 201
    assert response.json() == payload
    assert client.get("/transactions").json()[0] == payload


def test_transactions_require_authentication() -> None:
    app.dependency_overrides.pop(main.get_current_user_id)

    response = client.get("/transactions")

    assert response.status_code == 401
    assert response.json() == {"detail": "Missing authorization token"}


def test_transactions_are_isolated_by_user(fake_firestore) -> None:
    second_user_id = "second-user-456"
    app.dependency_overrides[main.get_current_user_id] = lambda: second_user_id
    payload = {
        "icon": "card",
        "merchant": "Private purchase",
        "meta": "Subscriptions • Credit",
        "amount": "- $4.99",
        "kind": "Expense",
    }

    assert client.put("/transactions", json=payload).status_code == 201
    assert client.get("/transactions").json() == [payload]
    assert len(fake_firestore[TEST_USER_ID]) == len(INITIAL_TRANSACTIONS)


def test_scan_receipt_returns_mock_data() -> None:
    response = client.post(
        "/receipts/scan",
        files={"file": ("receipt.jpg", b"mock image bytes", "image/jpeg")},
    )

    assert response.status_code == 200
    assert response.json()["merchant"] == "Aura Market"
    assert response.json()["amount"] == "- $34.25"
    assert response.json()["date"] == "2026-07-21"
    assert response.json()["kind"] == "Expense"
    assert response.json()["income"] is False


def test_scan_receipt_rejects_non_image() -> None:
    response = client.post(
        "/receipts/scan",
        files={"file": ("receipt.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 415
    assert response.json() == {"detail": "Receipt must be an image file"}


def test_scan_receipt_requires_authentication() -> None:
    app.dependency_overrides.pop(main.get_current_user_id)

    response = client.post(
        "/receipts/scan",
        files={"file": ("receipt.jpg", b"mock image bytes", "image/jpeg")},
    )

    assert response.status_code == 401
