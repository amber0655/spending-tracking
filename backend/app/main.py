import os
import logging
import hashlib
import json
from datetime import date as Date
from datetime import datetime as DateTime
from datetime import timedelta, timezone
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
InsightIconName = Literal[
    "coffee", "cash", "bag", "car", "home", "card", "dots", "arrowUp", "calendar"
]


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


class Insight(BaseModel):
    icon: InsightIconName = Field(description="UI icon that best represents this insight.")
    title: str = Field(
        min_length=1,
        max_length=80,
        description="Short, specific title for the insight card.",
    )
    value: str = Field(
        min_length=1,
        max_length=24,
        description="Compact amount, percentage, count, or trend label supported by the transactions.",
    )
    tone: Literal["good", "alert", "neutral"] = Field(
        description="Visual tone: good for positive patterns, alert for actionable overspending, neutral otherwise."
    )
    description: str = Field(
        min_length=1,
        max_length=320,
        description="Concise factual explanation and useful action based only on the supplied transactions.",
    )
    wide: bool = Field(
        default=False,
        description="True only for the single most important insight; false for other cards.",
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
INSIGHTS_CACHE_COLLECTION = "insight_cache"
Period = Literal["this_week", "this_month", "last_3_months", "this_year"]
InsightInterval = Literal["weekly", "monthly", "yearly"]
CACHE_DURATION = timedelta(hours=24)
INSIGHTS_CACHE_VERSION = 2
MAX_RECEIPT_BYTES = 15 * 1024 * 1024
RECEIPT_PROMPT = """Read this receipt image and extract its purchase as one Transaction.
Use only information visible in the image. Do not invent a merchant, total, or date.
Choose the most suitable category icon. The grand total must include tax and tip when shown.
Return only the structured result requested by the response schema."""


def insight_period(interval: InsightInterval) -> Period:
    return {
        "weekly": "this_week",
        "monthly": "this_month",
        "yearly": "this_year",
    }[interval]


def insight_prompt(
    interval: InsightInterval,
    start_date: Date,
    end_date: Date,
    transactions: list[Transaction],
) -> str:
    transaction_json = json.dumps(
        [item.model_dump(mode="json", exclude_none=True) for item in transactions],
        ensure_ascii=False,
    )
    return f"""Analyze these transactions for the user's current {interval} period ({start_date.isoformat()} through {end_date.isoformat()}).
Return 1 to 4 useful insights ordered by importance. Use only facts supported by the supplied transactions.
Do not claim knowledge of budgets, balances, savings rates, account activity, prior periods, or subscription usage.
Amounts in the input are display strings; treat negative amounts as expenses and positive amounts as income.
Always evaluate the largest individual expense and call it out when it is materially larger than the user's other transactions in this period.
Make at most one insight wide. Keep each description concise and actionable.

Transactions:
{transaction_json}"""


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


async def generate_insights_with_gemini(
    interval: InsightInterval,
    start_date: Date,
    end_date: Date,
    transactions: list[Transaction],
) -> list[Insight]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Insights are not configured: GEMINI_API_KEY is missing",
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
                contents=insight_prompt(interval, start_date, end_date, transactions),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=list[Insight],
                    temperature=0.2,
                ),
            )
            if isinstance(response.parsed, list):
                insights = [
                    item if isinstance(item, Insight) else Insight.model_validate(item)
                    for item in response.parsed
                ]
            elif response.text:
                insights = [Insight.model_validate(item) for item in json.loads(response.text)]
            else:
                raise ValueError("Gemini returned no structured insights")
            if not 1 <= len(insights) <= 4:
                raise ValueError("Gemini must return between 1 and 4 insights")
            return insights
        except genai_errors.ServerError as error:
            last_error = error
            logger.warning("Gemini model %s is unavailable for insights; trying fallback", model)
            continue
        except Exception as error:
            logger.exception("Gemini insight generation failed with model %s", model)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Gemini could not generate insights",
            ) from error

    logger.error("All Gemini insight models were unavailable: %s", last_error)
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Insights are temporarily busy. Please try again.",
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
    if period == "this_year":
        return current_date.replace(month=1, day=1)

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
    invalidate_insights_cache(user_id)


def insight_cache_document_id(user_id: str, interval: InsightInterval) -> str:
    digest = hashlib.sha256(user_id.encode()).hexdigest()
    return f"{digest}_{interval}_v{INSIGHTS_CACHE_VERSION}"


def invalidate_insights_cache(user_id: str) -> None:
    collection = firebase_db.collection(INSIGHTS_CACHE_COLLECTION)
    for interval in ("weekly", "monthly", "yearly"):
        collection.document(insight_cache_document_id(user_id, interval)).delete()


def insight_cache_is_valid(expires_at: object, now: DateTime) -> bool:
    if not isinstance(expires_at, DateTime):
        return False
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at > now


def get_cached_insights(
    user_id: str,
    interval: InsightInterval,
    now: DateTime | None = None,
) -> list[Insight] | None:
    snapshot = (
        firebase_db.collection(INSIGHTS_CACHE_COLLECTION)
        .document(insight_cache_document_id(user_id, interval))
        .get()
    )
    if not snapshot.exists:
        return None

    data = snapshot.to_dict()
    expires_at = data.get("expires_at")
    current_time = now or DateTime.now(timezone.utc)
    if not insight_cache_is_valid(expires_at, current_time):
        return None

    try:
        return [Insight.model_validate(item) for item in data.get("insights", [])]
    except Exception:
        logger.warning("Ignoring invalid insights cache for interval %s", interval)
        return None


def save_insights_cache(
    user_id: str,
    interval: InsightInterval,
    insights: list[Insight],
    now: DateTime | None = None,
) -> None:
    generated_at = now or DateTime.now(timezone.utc)
    (
        firebase_db.collection(INSIGHTS_CACHE_COLLECTION)
        .document(insight_cache_document_id(user_id, interval))
        .set(
            {
                "user_id": user_id,
                "interval": interval,
                "cache_version": INSIGHTS_CACHE_VERSION,
                "insights": [item.model_dump(mode="json") for item in insights],
                "generated_at": generated_at,
                "expires_at": generated_at + CACHE_DURATION,
            }
        )
    )


def insufficient_data_insight(transaction_count: int) -> Insight:
    return Insight(
        icon="dots",
        title="More data needed",
        value=f"{transaction_count} txn" if transaction_count == 1 else "No data",
        tone="neutral",
        description="Add at least two transactions in this period to unlock personalized spending insights.",
        wide=True,
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


@app.get(
    "/insights",
    response_model=list[Insight],
)
async def get_insights(
    interval: InsightInterval = "monthly",
    user_id: str = Depends(get_current_user_id),
) -> list[Insight]:
    cached = get_cached_insights(user_id, interval)
    if cached is not None:
        return cached

    period = insight_period(interval)
    start_date = period_start(period)
    transactions = list_transactions(user_id, period)
    if len(transactions) < 2:
        insights = [insufficient_data_insight(len(transactions))]
    else:
        insights = await generate_insights_with_gemini(
            interval,
            start_date,
            Date.today(),
            transactions,
        )
    save_insights_cache(user_id, interval, insights)
    return insights


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
