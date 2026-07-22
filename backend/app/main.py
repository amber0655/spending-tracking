import os
import logging
from datetime import date as Date
from datetime import datetime as DateTime
from datetime import timedelta
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import auth, firestore
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from app.firebase import firebase_app, firebase_db


load_dotenv()
logger = logging.getLogger(__name__)
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
    icon: IconName = Field(
        description="UI icon inferred from the purchase: coffee for dining, bag for shopping, car for transport, home for housing or utilities, card for subscriptions, and dots when uncertain."
    )
    merchant: str = Field(
        min_length=1,
        max_length=200,
        description="Merchant or store name printed on the receipt, without address or slogan.",
    )
    meta: str = Field(
        min_length=1,
        max_length=200,
        description="Short display metadata in the format 'Category • Receipt', for example 'Dining • Receipt'.",
    )
    amount: str = Field(
        min_length=1,
        max_length=50,
        description="Receipt grand total as a negative US-dollar display string with exactly two decimals, for example '- $18.45'.",
    )
    kind: str = Field(
        min_length=1,
        max_length=50,
        description="Transaction type. Use 'Expense' for a purchase receipt.",
    )
    income: bool | None = Field(
        default=None,
        description="Whether this transaction is income. Use false for a purchase receipt.",
    )
    date: Date | None = Field(
        default=None,
        description="Purchase date printed on the receipt in YYYY-MM-DD form; null if it is not visible or cannot be determined.",
    )


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
MAX_RECEIPT_BYTES = 15 * 1024 * 1024
RECEIPT_PROMPT = """Read this receipt image and extract its purchase as one Transaction.
Use only information visible in the image. Do not invent a merchant, total, or date.
Choose the most suitable category icon. The grand total must include tax and tip when shown.
Return only the structured result requested by the response schema."""


async def parse_receipt_with_gemini(image: bytes, mime_type: str) -> Transaction:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Receipt scanning is not configured: GEMINI_API_KEY is missing",
        )

    client = genai.Client(api_key=api_key)
    primary_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    fallback_model = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash-lite")
    models = list(dict.fromkeys([primary_model, fallback_model]))
    last_error: Exception | None = None

    for model in models:
        try:
            response = await client.aio.models.generate_content(
                model=model,
                contents=[
                    RECEIPT_PROMPT,
                    types.Part.from_bytes(data=image, mime_type=mime_type),
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=Transaction,
                    temperature=0,
                ),
            )
            if isinstance(response.parsed, Transaction):
                return response.parsed
            if response.text:
                return Transaction.model_validate_json(response.text)
            raise ValueError("Gemini returned no structured transaction")
        except genai_errors.ServerError as error:
            last_error = error
            logger.warning("Gemini model %s is unavailable; trying fallback", model)
            continue
        except Exception as error:
            logger.exception("Gemini receipt parsing failed with model %s", model)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Gemini could not parse this receipt",
            ) from error

    logger.error("All Gemini receipt models were unavailable: %s", last_error)
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Receipt scanning is temporarily busy. Please try again.",
    ) from last_error


def get_current_user_id(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
        )

    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )

    try:
        decoded_token = auth.verify_id_token(token)
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authorization token",
        ) from error

    user_id = decoded_token.get("uid")
    if not isinstance(user_id, str) or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token has no user ID",
        )

    return user_id


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


def list_transactions(user_id: str, period: Period = "this_month") -> list[Transaction]:
    start_date = period_start(period)
    documents = (
        firebase_db.collection(TRANSACTIONS_COLLECTION)
        .where("user_id", "==", user_id)
        .stream()
    )
    results: list[tuple[str, Transaction]] = []
    for document in documents:
        data = document.to_dict()
        transaction_date = document_date(data)
        if transaction_date is not None and transaction_date >= start_date:
            results.append((str(data.get("created_at", "")), Transaction.model_validate(data)))
    results.sort(key=lambda item: item[0], reverse=True)
    return [transaction for _, transaction in results]


def save_transaction(user_id: str, transaction: Transaction) -> None:
    firebase_db.collection(TRANSACTIONS_COLLECTION).add(
        {
            **transaction.model_dump(mode="json", exclude_none=True),
            "user_id": user_id,
            "created_at": firestore.SERVER_TIMESTAMP,
        }
    )


@app.get(
    "/transactions",
    response_model=list[Transaction],
    response_model_exclude_none=True,
)
def get_transactions(
    period: Period = "this_month",
    user_id: str = Depends(get_current_user_id),
) -> list[Transaction]:
    return list_transactions(user_id, period)


@app.post(
    "/transactions",
    response_model=Transaction,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
)
def create_transaction(
    payload: Transaction,
    user_id: str = Depends(get_current_user_id),
) -> Transaction:
    save_transaction(user_id, payload)
    return payload


@app.put(
    "/transactions",
    response_model=Transaction,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
)
def put_transaction(
    payload: Transaction,
    user_id: str = Depends(get_current_user_id),
) -> Transaction:
    save_transaction(user_id, payload)
    return payload


@app.post("/receipts/scan", response_model=Transaction, response_model_exclude_none=True)
async def scan_receipt(
    file: Annotated[UploadFile, File(description="Receipt image")],
    _user_id: str = Depends(get_current_user_id),
) -> Transaction:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Receipt must be an image file",
        )

    image = await file.read(MAX_RECEIPT_BYTES + 1)
    await file.close()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Receipt image is empty",
        )
    if len(image) > MAX_RECEIPT_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Receipt image must be 15 MB or smaller",
        )

    return await parse_receipt_with_gemini(image, file.content_type)
