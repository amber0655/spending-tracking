import type { Transaction } from '../components/TransactionRow'
import { auth } from './firebase'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export type TransactionPeriod = 'this_week' | 'this_month' | 'last_3_months'

async function authenticatedFetch(input: string, init: RequestInit = {}) {
  const user = auth.currentUser
  if (!user) throw new Error('You must be signed in to access transactions.')

  const request = async (forceRefresh = false) => {
    const token = await user.getIdToken(forceRefresh)
    const headers = new Headers(init.headers)
    headers.set('Authorization', `Bearer ${token}`)
    return fetch(input, { ...init, headers })
  }

  let response = await request()
  if (response.status === 401) response = await request(true)
  return response
}

export async function getTransactions(
  period: TransactionPeriod,
  signal?: AbortSignal,
): Promise<Transaction[]> {
  const params = new URLSearchParams({ period })
  const response = await authenticatedFetch(`${API_BASE_URL}/transactions?${params}`, { signal })

  if (!response.ok) {
    throw new Error(`Unable to load transactions (${response.status})`)
  }

  return response.json() as Promise<Transaction[]>
}

export async function putTransaction(transaction: Transaction): Promise<Transaction> {
  const response = await authenticatedFetch(`${API_BASE_URL}/transactions`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(transaction),
  })

  if (!response.ok) {
    throw new Error(`Unable to add expense (${response.status})`)
  }

  return response.json() as Promise<Transaction>
}
