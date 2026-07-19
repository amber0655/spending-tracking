import pytest
from datetime import date
from fastapi.testclient import TestClient

from app import main
from app.main import INITIAL_TRANSACTIONS, Transaction, app, period_start


client = TestClient(app)


@pytest.fixture(autouse=True)
def fake_firestore(monkeypatch) -> list[Transaction]:
    records = [item.model_copy() for item in INITIAL_TRANSACTIONS]
    monkeypatch.setattr(main, "list_transactions", lambda period="this_month": records)
    monkeypatch.setattr(main, "save_transaction", lambda item: records.insert(0, item))
    return records


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
