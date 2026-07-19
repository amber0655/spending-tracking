from datetime import date as Date
from datetime import datetime as DateTime
from datetime import timedelta
from typing import Literal

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import firestore
from pydantic import BaseModel, Field

from app.firebase import firebase_app, firebase_db


app = FastAPI(title="Spending Tracker API")
app.state.firebase_app = firebase_app
app.state.firebase_db = firebase_db
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["*"],
)

IconName = Literal["coffee", "cash", "bag", "car", "home", "card", "dots"]


class Transaction(BaseModel):
    icon: IconName
    merchant: str = Field(min_length=1, max_length=200)
    meta: str = Field(min_length=1, max_length=200)
    amount: str = Field(min_length=1, max_length=50)
    kind: str = Field(min_length=1, max_length=50)
    income: bool | None = None
    date: Date | None = None


INITIAL_TRANSACTIONS = [
    Transaction(
        icon="coffee",
        merchant="Sweetgreen",
        meta="Food & Dining • Credit",
        amount="- $18.45",
        kind="Expense",
    ),
    Transaction(
        icon="coffee",
        merchant="Blue Bottle Coffee",
        meta="Food & Dining • Debit",
        amount="- $6.50",
        kind="Expense",
    ),
    Transaction(
        icon="cash",
        merchant="Acme Corp Payroll",
        meta="Income • Direct Deposit",
        amount="+ $3,250.00",
        kind="Income",
        income=True,
    ),
    Transaction(
        icon="bag",
        merchant="Everlane",
        meta="Shopping • Credit",
        amount="- $145.00",
        kind="Expense",
    ),
    Transaction(
        icon="car",
        merchant="Uber",
        meta="Transport • Debit",
        amount="- $24.80",
        kind="Expense",
    ),
    Transaction(
        icon="home",
        merchant="PG&E Energy",
        meta="Housing & Utilities • Auto-pay",
        amount="- $89.20",
        kind="Expense",
    ),
]

TRANSACTIONS_COLLECTION = "transactions"
Period = Literal["this_week", "this_month", "last_3_months"]


def period_start(period: Period, today: Date | None = None) -> Date:
    current_date = today or Date.today()
    if period == "this_week":
        return current_date - timedelta(days=current_date.weekday())
    if period == "this_month":
        return current_date.replace(day=1)

    month_index = current_date.year * 12 + current_date.month - 3
    return Date(month_index // 12, month_index % 12 + 1, 1)


def document_date(data: dict) -> Date | None:
    transaction_date = data.get("date")
    if isinstance(transaction_date, str):
        return Date.fromisoformat(transaction_date)
    if isinstance(transaction_date, DateTime):
        return transaction_date.date()

    created_at = data.get("created_at")
    return created_at.date() if isinstance(created_at, DateTime) else None


def list_transactions(period: Period = "this_month") -> list[Transaction]:
    start_date = period_start(period)
    documents = (
        firebase_db.collection(TRANSACTIONS_COLLECTION)
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .stream()
    )
    results = []
    for document in documents:
        data = document.to_dict()
        transaction_date = document_date(data)
        if transaction_date is not None and transaction_date >= start_date:
            results.append(Transaction.model_validate(data))
    return results


def save_transaction(transaction: Transaction) -> None:
    firebase_db.collection(TRANSACTIONS_COLLECTION).add(
        {
            **transaction.model_dump(mode="json", exclude_none=True),
            "created_at": firestore.SERVER_TIMESTAMP,
        }
    )


@app.get(
    "/transactions",
    response_model=list[Transaction],
    response_model_exclude_none=True,
)
def get_transactions(period: Period = "this_month") -> list[Transaction]:
    return list_transactions(period)


@app.post(
    "/transactions",
    response_model=Transaction,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
)
def create_transaction(payload: Transaction) -> Transaction:
    save_transaction(payload)
    return payload


@app.put(
    "/transactions",
    response_model=Transaction,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
)
def put_transaction(payload: Transaction) -> Transaction:
    save_transaction(payload)
    return payload
