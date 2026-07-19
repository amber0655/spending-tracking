import { useEffect, useState } from 'react'
import { AppHeader, BottomNav } from '../components/AppShell'
import { Icon } from '../components/Icon'
import { TransactionRow, type Transaction } from '../components/TransactionRow'
import { getTransactions, type TransactionPeriod } from '../lib/transactionsApi'

const periods: Array<{ label: string; value: TransactionPeriod }> = [
  { label: 'This Month', value: 'this_month' },
  { label: 'This Week', value: 'this_week' },
  { label: 'Last 3 Months', value: 'last_3_months' },
]

export function TransactionsPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [query, setQuery] = useState('')
  const [period, setPeriod] = useState<TransactionPeriod>('this_month')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true

    const loadTransactions = () => {
      getTransactions(period)
        .then((items) => {
          if (!active) return
          setTransactions(items)
          setError(null)
        })
        .catch((requestError: unknown) => {
          if (active) {
            setError(requestError instanceof Error ? requestError.message : 'Unable to load transactions')
          }
        })
        .finally(() => {
          if (active) setLoading(false)
        })
    }

    const refreshWhenVisible = () => {
      if (document.visibilityState === 'visible') loadTransactions()
    }

    loadTransactions()
    window.addEventListener('focus', loadTransactions)
    document.addEventListener('visibilitychange', refreshWhenVisible)

    return () => {
      active = false
      window.removeEventListener('focus', loadTransactions)
      document.removeEventListener('visibilitychange', refreshWhenVisible)
    }
  }, [period])

  const normalizedQuery = query.trim().toLowerCase()
  const visibleTransactions = transactions.filter((transaction) =>
    transaction.merchant.toLowerCase().includes(normalizedQuery),
  )

  return (
    <div className="min-h-screen bg-[#f7f9fb]">
      <AppHeader />
      <main className="mx-auto max-w-5xl px-5 pb-28 pt-24 sm:px-8">
        <h2 className="text-3xl font-semibold">Transactions</h2>
        <p className="mt-2 text-[#5c5d64]">Review your recent mindful spending.</p>
        <div className="transaction-search mt-7">
          <Icon name="search" className="size-5" />
          <input
            aria-label="Search merchants"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search merchants..."
          />
          {query && (
            <button
              type="button"
              onClick={() => setQuery('')}
              className="text-sm font-medium text-[#5c5d64] hover:text-black"
            >
              Clear
            </button>
          )}
        </div>
        <div className="scrollbar-none mt-4 flex gap-2 overflow-x-auto">
          {periods.map((option) => (
            <button
              key={option.value}
              onClick={() => setPeriod(option.value)}
              className={`period-chip ${period === option.value ? 'period-chip--active' : ''}`}
            >
              {option.label}
            </button>
          ))}
        </div>
        <section className="transaction-list mt-6">
          {loading && <div className="p-16 text-center">Loading transactions...</div>}
          {!loading && error && (
            <div className="p-16 text-center text-red-700">{error}</div>
          )}
          {!loading && !error && visibleTransactions.length > 0 && (
            <div>
              <h3 className="transaction-date">
                {normalizedQuery
                  ? `${visibleTransactions.length} merchant${visibleTransactions.length === 1 ? '' : 's'} found`
                  : 'All transactions'}
              </h3>
              {visibleTransactions.map((transaction, index) => (
                <TransactionRow
                  key={`${transaction.merchant}-${transaction.amount}-${index}`}
                  transaction={transaction}
                />
              ))}
            </div>
          )}
          {!loading && !error && visibleTransactions.length === 0 && (
            <div className="p-16 text-center">No matching transactions</div>
          )}
        </section>
      </main>
      <BottomNav active="transactions" />
    </div>
  )
}
