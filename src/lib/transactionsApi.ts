import type { Transaction } from '../components/TransactionRow'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export type TransactionPeriod = 'this_week' | 'this_month' | 'last_3_months'

export async function getTransactions(
  period: TransactionPeriod,
  signal?: AbortSignal,
): Promise<Transaction[]> {
  const params = new URLSearchParams({ period })
  const response = await fetch(`${API_BASE_URL}/transactions?${params}`, { signal })

  if (!response.ok) {
    throw new Error(`Unable to load transactions (${response.status})`)
  }

  return response.json() as Promise<Transaction[]>
}

export async function putTransaction(transaction: Transaction): Promise<Transaction> {
  const response = await fetch(`${API_BASE_URL}/transactions`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(transaction),
  })

  if (!response.ok) {
    throw new Error(`Unable to add expense (${response.status})`)
  }

  return response.json() as Promise<Transaction>
}
