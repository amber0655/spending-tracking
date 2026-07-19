import { type FormEvent, useState } from 'react'
import { AppHeader, BottomNav } from '../components/AppShell'
import { Icon, type IconName } from '../components/Icon'
import { putTransaction } from '../lib/transactionsApi'

const categories: Array<{ label: string; icon: IconName }> = [
  { label: 'Dining', icon: 'coffee' },
  { label: 'Shopping', icon: 'bag' },
  { label: 'Transport', icon: 'car' },
  { label: 'Bills', icon: 'home' },
  { label: 'Other', icon: 'dots' },
]

export function ManualExpensePage() {
  const [category, setCategory] = useState('Dining')
  const [amount, setAmount] = useState('')
  const [date, setDate] = useState('2026-07-18')
  const [notes, setNotes] = useState('')
  const [saved, setSaved] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)

    const selectedCategory = categories.find((item) => item.label === category)!

    try {
      await putTransaction({
        icon: selectedCategory.icon,
        merchant: notes.trim() || `${category} expense`,
        meta: `${category} • ${date}`,
        amount: `- $${Number(amount).toFixed(2)}`,
        kind: 'Expense',
        income: false,
        date,
      })
      setSaved(true)
      setAmount('')
      setNotes('')
      window.setTimeout(() => setSaved(false), 1800)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to add expense')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#f7f9fb]">
      <AppHeader />
      <main className="mx-auto max-w-2xl px-5 pb-28 pt-24 sm:px-8">
        <h2 className="text-3xl font-semibold">Record Expense</h2>
        <p className="mt-2 text-sm text-[#5c5d64]">Stay mindful of your spending habits.</p>
        <form onSubmit={submit} className="mt-6">
          <section className="amount-card">
            <label className="eyebrow" htmlFor="amount">Amount</label>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-5xl font-bold">$</span>
              <input
                id="amount"
                type="number"
                min="0.01"
                step=".01"
                value={amount}
                onChange={(event) => setAmount(event.target.value)}
                placeholder="0.00"
                required
                className="amount-input"
              />
            </div>
          </section>
          <section className="mt-7">
            <p className="eyebrow mb-3">Category</p>
            <div className="flex flex-wrap gap-2">
              {categories.map((item) => (
                <button
                  key={item.label}
                  type="button"
                  onClick={() => setCategory(item.label)}
                  className={`category-chip ${category === item.label ? 'category-chip--active' : ''}`}
                >
                  <Icon name={item.icon} className="size-[18px]" />
                  {item.label}
                </button>
              ))}
            </div>
          </section>
          <section className="mt-7 grid gap-5 sm:grid-cols-2">
            <label className="space-y-2">
              <span className="eyebrow block">Date</span>
              <input
                type="date"
                value={date}
                onChange={(event) => setDate(event.target.value)}
                required
                className="expense-input"
              />
            </label>
            <label className="space-y-2">
              <span className="eyebrow block">Notes (optional)</span>
              <input
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                placeholder="Dinner with colleagues"
                className="expense-input"
              />
            </label>
          </section>
          {error && <p className="mt-4 text-sm text-red-700">{error}</p>}
          <button
            disabled={submitting}
            className={`expense-submit ${saved ? 'expense-submit--saved' : ''}`}
          >
            <Icon name={saved ? 'check' : 'plus'} className="size-5" />
            {submitting ? 'Adding...' : saved ? 'Expense added' : 'Add Expense'}
          </button>
        </form>
        <aside className="tip-card">
          <div className="grid size-10 place-items-center rounded-xl bg-[#00865d] text-white">
            <Icon name="bulb" className="size-5" />
          </div>
          <div>
            <h3 className="font-semibold text-[#005236]">Spending Tip</h3>
            <p className="mt-1 text-sm text-[#006c49]">You've stayed within your daily budget for 5 days straight. Keeping this entry under $40 will maintain your streak!</p>
          </div>
        </aside>
      </main>
      <BottomNav active="expense" />
    </div>
  )
}
