import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AppHeader, BottomNav } from '../components/AppShell'
import { Icon } from '../components/Icon'
import { TransactionRow, type Transaction } from '../components/TransactionRow'
import { getTransactions } from '../lib/transactionsApi'

const currency = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
})

function amountValue(amount: string) {
  const value = Number(amount.replace(/[^0-9.-]/g, ''))
  return Number.isFinite(value) ? Math.abs(value) : 0
}

function isExpense(transaction: Transaction) {
  return transaction.income !== true && !transaction.amount.trim().startsWith('+')
}

function monthKey(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
}

function transactionMonth(transaction: Transaction) {
  return transaction.date?.slice(0, 7) ?? ''
}

function Comparison({
  label,
  amount,
  width,
  active = false,
}: {
  label: string
  amount: number
  width: number
  active?: boolean
}) {
  return (
    <div>
      <div className="mb-2 flex justify-between">
        <span className="text-sm text-[#5c5d64]">{label}</span>
        <span className={`font-mono text-sm ${active ? 'text-[#00714d]' : ''}`}>
          {currency.format(amount)}
        </span>
      </div>
      <div className="h-2 rounded-full bg-[#f2f4f6]">
        <div
          className={`h-full rounded-full ${active ? 'bg-[#00865d]' : 'bg-[#c6c6cd]'}`}
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  )
}

export function DashboardPage() {
  const [open, setOpen] = useState(false)
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [reloadKey, setReloadKey] = useState(0)
  const navigate = useNavigate()

  useEffect(() => {
    const controller = new AbortController()

    getTransactions('last_3_months', controller.signal)
      .then(setTransactions)
      .catch((requestError) => {
        if (requestError instanceof DOMException && requestError.name === 'AbortError') return
        setError(requestError instanceof Error ? requestError.message : 'Unable to load your spending data.')
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })

    return () => controller.abort()
  }, [reloadKey])

  const summary = useMemo(() => {
    const now = new Date()
    const previousMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1)
    const currentKey = monthKey(now)
    const previousKey = monthKey(previousMonth)
    const expenses = transactions.filter(isExpense)
    const currentExpenses = expenses.filter((item) => transactionMonth(item) === currentKey)
    const current = currentExpenses.reduce((total, item) => total + amountValue(item.amount), 0)
    const previous = expenses
      .filter((item) => transactionMonth(item) === previousKey)
      .reduce((total, item) => total + amountValue(item.amount), 0)
    const difference = current - previous
    const percentage = previous > 0 ? Math.abs((difference / previous) * 100) : null
    const maxComparison = Math.max(current, previous, 1)
    const daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate()
    const buckets = Array.from({ length: 7 }, () => 0)

    for (const transaction of currentExpenses) {
      if (!transaction.date) continue
      const day = Number(transaction.date.slice(8, 10))
      const bucket = Math.min(6, Math.floor(((day - 1) / daysInMonth) * 7))
      buckets[bucket] += amountValue(transaction.amount)
    }
    const maxBucket = Math.max(...buckets, 1)

    return {
      current,
      previous,
      difference,
      percentage,
      currentWidth: (current / maxComparison) * 100,
      previousWidth: (previous / maxComparison) * 100,
      bars: buckets.map((value) => value === 0 ? 6 : Math.max(12, (value / maxBucket) * 100)),
    }
  }, [transactions])

  const recentTransactions = transactions.slice(0, 5)
  const spendingLess = summary.difference <= 0

  function retry() {
    setLoading(true)
    setError('')
    setReloadKey((key) => key + 1)
  }

  return (
    <div className="min-h-screen bg-[#f7f9fb]">
      <AppHeader />
      <main className="mx-auto max-w-7xl px-5 pb-28 pt-24 sm:px-8">
        {error && (
          <div role="alert" className="mb-6 flex items-center justify-between gap-4 rounded-xl bg-[#ffdad6] px-4 py-3 text-sm text-[#93000a]">
            <span>{error}</span>
            <button type="button" onClick={retry} className="font-semibold underline">Retry</button>
          </div>
        )}

        <section className="mb-8 grid gap-6 lg:grid-cols-3">
          <article className="summary-card relative overflow-hidden lg:col-span-2">
            <p className="eyebrow">Your spending this month</p>
            <div className="mt-3 flex flex-wrap items-center gap-3">
              <strong className="text-[40px] font-bold sm:text-5xl">
                {loading ? '—' : currency.format(summary.current)}
              </strong>
              {!loading && summary.percentage !== null && (
                <span className="trend-pill">
                  <Icon name={spendingLess ? 'trendDown' : 'arrowUp'} className="size-4" />
                  {summary.percentage.toFixed(1)}%
                </span>
              )}
            </div>
            <div aria-label="Spending distribution this month" className="mt-10 flex h-32 items-end gap-2">
              {summary.bars.map((height, index) => (
                <span
                  key={index}
                  className={`flex-1 rounded-t-lg ${height === Math.max(...summary.bars) && summary.current > 0 ? 'bg-black' : 'bg-[#e0e3e5]'}`}
                  style={{ height: `${height}%` }}
                />
              ))}
            </div>
          </article>

          <article className="summary-card border-l-4 border-l-[#00865d]">
            <p className="eyebrow">Your monthly comparison</p>
            <div className="mt-5 space-y-4">
              <Comparison label="Last Month" amount={summary.previous} width={summary.previousWidth} />
              <Comparison label="Current" amount={summary.current} width={summary.currentWidth} active />
            </div>
            {!loading && (
              <p className="mt-7 text-sm leading-6 text-[#5c5d64]">
                {summary.previous === 0
                  ? summary.current === 0
                    ? 'Add your first expense to start tracking your monthly spending.'
                    : 'This is your first month with recorded spending data.'
                  : <>{`You've spent `}<strong className="text-black">{currency.format(Math.abs(summary.difference))} {spendingLess ? 'less' : 'more'}</strong>{' than last month.'}</>}
              </p>
            )}
          </article>
        </section>

        <section>
          <div className="mb-3 flex justify-between">
            <h2 className="text-xl font-semibold">Your Recent Transactions</h2>
            <button type="button" onClick={() => navigate('/transactions')} className="text-xs font-semibold uppercase text-[#00714d]">View all</button>
          </div>
          <div className="overflow-hidden rounded-2xl border bg-white">
            {loading && <p className="px-5 py-10 text-center text-sm text-[#67686f]">Loading your transactions…</p>}
            {!loading && recentTransactions.length === 0 && <p className="px-5 py-10 text-center text-sm text-[#67686f]">No transactions yet. Add an expense to see it here.</p>}
            {!loading && recentTransactions.map((transaction, index) => (
              <TransactionRow key={`${transaction.merchant}-${transaction.date ?? index}-${index}`} transaction={transaction} />
            ))}
          </div>
        </section>
      </main>

      <div className={`fab-menu ${open ? 'fab-menu--open' : ''}`}>
        <button type="button" onClick={() => navigate('/receipts/scan')}><span>Scan Receipt</span><Icon name="scan" className="size-5" /></button>
        <button type="button" onClick={() => navigate('/expenses/new')}><span>Manual Entry</span><Icon name="plus" className="size-5" /></button>
      </div>
      <button type="button" aria-label="Open quick actions" onClick={() => setOpen((value) => !value)} className="fab">
        <Icon name={open ? 'plus' : 'scan'} className="size-7" />
      </button>
      <BottomNav active="home" />
    </div>
  )
}
