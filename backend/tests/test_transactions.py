import pytest
from datetime import date, datetime, timedelta, timezone
from fastapi.testclient import TestClient

from app import main
from app.main import INITIAL_TRANSACTIONS, Insight, Transaction, app, period_start


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
    insight_cache: dict[tuple[str, str], list[Insight]] = {}

    monkeypatch.setattr(
        main,
        "get_cached_insights",
        lambda user_id, interval: insight_cache.get((user_id, interval)),
    )
    monkeypatch.setattr(
        main,
        "save_insights_cache",
        lambda user_id, interval, insights: insight_cache.__setitem__(
            (user_id, interval), insights
        ),
    )

    async def fake_insight_generator(
        _interval, _start_date, _end_date, _transactions
    ) -> list[Insight]:
        return [
            Insight(
                icon="coffee",
                title="Dining concentration",
                value="$24.95",
                tone="neutral",
                description="Dining is the largest category in this period.",
                wide=True,
            )
        ]

    monkeypatch.setattr(main, "generate_insights_with_gemini", fake_insight_generator)
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
    assert period_start("this_year", today) == date(2026, 1, 1)


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


@pytest.mark.parametrize("interval", ["weekly", "monthly", "yearly"])
def test_get_insights_for_each_interval(interval: str) -> None:
    response = client.get("/insights", params={"interval": interval})

    assert response.status_code == 200
    assert response.json()[0]["title"] == "Dining concentration"
    assert response.json()[0]["wide"] is True


def test_insights_require_authentication() -> None:
    app.dependency_overrides.pop(main.get_current_user_id)

    response = client.get("/insights")

    assert response.status_code == 401


def test_insights_query_current_user_only(monkeypatch) -> None:
    second_user_id = "insights-user-456"
    requested_users: list[str] = []
    app.dependency_overrides[main.get_current_user_id] = lambda: second_user_id

    def record_user(user_id, _period):
        requested_users.append(user_id)
        return INITIAL_TRANSACTIONS

    monkeypatch.setattr(main, "list_transactions", record_user)

    response = client.get("/insights", params={"interval": "monthly"})

    assert response.status_code == 200
    assert requested_users == [second_user_id]


def test_insights_reject_invalid_interval() -> None:
    response = client.get("/insights", params={"interval": "daily"})

    assert response.status_code == 422


def test_insights_with_insufficient_data_skip_gemini(monkeypatch) -> None:
    monkeypatch.setattr(main, "list_transactions", lambda _user_id, _period: [])

    async def fail_if_called(*_args):
        raise AssertionError("Gemini should not be called")

    monkeypatch.setattr(main, "generate_insights_with_gemini", fail_if_called)

    response = client.get("/insights", params={"interval": "weekly"})

    assert response.status_code == 200
    assert response.json()[0]["title"] == "More data needed"


def test_insights_use_cache(monkeypatch) -> None:
    calls = 0
    cached: list[Insight] | None = None

    async def count_generation(*_args) -> list[Insight]:
        nonlocal calls
        calls += 1
        return [
            Insight(
                icon="bag",
                title="Shopping pattern",
                value="4 txns",
                tone="neutral",
                description="Four shopping transactions were recorded.",
            )
        ]

    def get_cache(_user_id, _interval):
        return cached

    def save_cache(_user_id, _interval, insights):
        nonlocal cached
        cached = insights

    monkeypatch.setattr(main, "generate_insights_with_gemini", count_generation)
    monkeypatch.setattr(main, "get_cached_insights", get_cache)
    monkeypatch.setattr(main, "save_insights_cache", save_cache)

    assert client.get("/insights").status_code == 200
    assert client.get("/insights").status_code == 200
    assert calls == 1


def test_insight_cache_expires_after_24_hours() -> None:
    generated_at = datetime(2026, 7, 22, tzinfo=timezone.utc)

    assert main.insight_cache_is_valid(
        generated_at + timedelta(hours=24),
        generated_at + timedelta(hours=23, minutes=59),
    )
    assert not main.insight_cache_is_valid(
        generated_at + timedelta(hours=24),
        generated_at + timedelta(hours=24),
    )


def test_transaction_write_invalidates_all_insight_intervals(monkeypatch) -> None:
    deleted: list[str] = []

    class FakeDocument:
        def __init__(self, document_id: str):
            self.document_id = document_id

        def delete(self) -> None:
            deleted.append(self.document_id)

    class FakeCollection:
        def document(self, document_id: str) -> FakeDocument:
            return FakeDocument(document_id)

    class FakeDatabase:
        def collection(self, _name: str) -> FakeCollection:
            return FakeCollection()

    monkeypatch.setattr(main, "firebase_db", FakeDatabase())

    main.invalidate_insights_cache(TEST_USER_ID)

    assert deleted == [
        main.insight_cache_document_id(TEST_USER_ID, "weekly"),
        main.insight_cache_document_id(TEST_USER_ID, "monthly"),
        main.insight_cache_document_id(TEST_USER_ID, "yearly"),
    ]
