# Spending Tracker API

Install dependencies and start the development server:

```bash
uv sync
uv run uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`. Interactive documentation is available
at `http://127.0.0.1:8000/docs`.

For production, set `CORS_ORIGINS` to the deployed frontend origin. Multiple
origins can be separated with commas:

```bash
CORS_ORIGINS=https://spending-tracking.onrender.com
```

Copy `.env.example` to `.env` and add a Gemini API key to enable receipt scans:

```bash
cp .env.example .env
```

`POST /receipts/scan` accepts an authenticated multipart image upload in the
`file` field. Gemini reads the image bytes and returns a structured
`Transaction`. The default model is `gemini-2.5-flash`; override it with
`GEMINI_MODEL` if needed.
If the primary model is temporarily unavailable, the server retries with
`GEMINI_FALLBACK_MODEL` (default: `gemini-3.5-flash-lite`).

Firebase Admin is initialized when the API starts. On Render, copy each field
from the service-account JSON into the corresponding `FIREBASE_*` environment
variable shown in `.env.example`. Store `FIREBASE_PRIVATE_KEY` on one line with
literal `\n` sequences; the backend converts them to real newlines.

For local development, the service-account file remains supported as a
fallback:

```bash
export FIREBASE_SERVICE_ACCOUNT=/absolute/path/to/serviceAccountKey.json
```

The initialized Firebase app and Firestore client are available as
`app.firebase.firebase_app` and `app.firebase.firebase_db`. Transactions are
stored in the `transactions` Firestore collection.

Create a transaction:

```bash
curl -X POST http://127.0.0.1:8000/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $FIREBASE_ID_TOKEN" \
  -d '{
    "icon": "card",
    "merchant": "Cloud Storage",
    "meta": "Subscriptions • Credit",
    "amount": "- $9.99",
    "kind": "Expense"
  }'
```

List transactions:

```bash
curl http://127.0.0.1:8000/transactions \
  -H "Authorization: Bearer $FIREBASE_ID_TOKEN"
```

Filter by period with `this_week`, `this_month`, or `last_3_months`:

```bash
curl "http://127.0.0.1:8000/transactions?period=this_week" \
  -H "Authorization: Bearer $FIREBASE_ID_TOKEN"
```

Every endpoint verifies the Firebase ID token. Transactions persist in Cloud
Firestore with the verified Firebase `uid` and are only returned to that user.

Generate personalized insights for the current natural week, month, or year:

```bash
curl "http://127.0.0.1:8000/insights?interval=monthly" \
  -H "Authorization: Bearer $FIREBASE_ID_TOKEN"
```

The response is an array of structured insight cards. Results are cached in
Firestore for 24 hours per user and interval. Creating a transaction clears
that user's weekly, monthly, and yearly caches so the next request includes the
new expense. Periods with fewer than two transactions return a deterministic
“More data needed” card without calling Gemini.
