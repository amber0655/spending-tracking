import { useEffect, useState } from 'react'
import { AppHeader, BottomNav } from '../components/AppShell'
import { Icon } from '../components/Icon'
import { getInsights, type Insight, type InsightInterval } from '../lib/insightsApi'

const periods: Array<{ label: string; value: InsightInterval }> = [
  { label: 'Weekly', value: 'weekly' },
  { label: 'Monthly', value: 'monthly' },
  { label: 'Yearly', value: 'yearly' },
]

export function InsightsPage() {
  const [period, setPeriod] = useState<InsightInterval>('monthly')
  const [insights, setInsights] = useState<Insight[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    const controller = new AbortController()

    getInsights(period, controller.signal)
      .then(setInsights)
      .catch((requestError) => {
        if (requestError instanceof DOMException && requestError.name === 'AbortError') return
        setError(requestError instanceof Error ? requestError.message : 'Unable to load insights.')
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })

    return () => controller.abort()
  }, [period, reloadKey])

  function choosePeriod(nextPeriod: InsightInterval) {
    if (nextPeriod === period) return
    setPeriod(nextPeriod)
    setInsights([])
    setError('')
    setLoading(true)
  }

  function retry() {
    setError('')
    setLoading(true)
    setReloadKey((key) => key + 1)
  }

  return (
    <div className="min-h-screen bg-[#f7f9fb]">
      <AppHeader />
      <main className="mx-auto max-w-6xl px-5 pb-28 pt-24 sm:px-8">
        <p className="eyebrow text-[#71809a]">Your financial overview</p>
        <h2 className="mt-2 text-3xl font-semibold">Smart Insights</h2>

        <div className="segmented-control mt-4" aria-label="Insight interval">
          {periods.map((option) => (
            <button
              type="button"
              key={option.value}
              aria-pressed={period === option.value}
              onClick={() => choosePeriod(option.value)}
              className={period === option.value ? 'is-active' : ''}
            >
              {option.label}
            </button>
          ))}
        </div>

        {error && (
          <div role="alert" className="mt-6 rounded-2xl bg-[#ffdad6] px-5 py-4 text-sm text-[#93000a]">
            <p>{error}</p>
            <button type="button" onClick={retry} className="mt-2 font-semibold underline">Try again</button>
          </div>
        )}

        {loading && (
          <section className="insights-grid mt-6" aria-label="Loading insights">
            {[0, 1, 2].map((index) => (
              <article key={index} className={`insight-card animate-pulse ${index === 0 ? 'insight-card--wide' : ''}`}>
                <div className="size-12 rounded-xl bg-[#e0e3e5]" />
                <div className="mt-6 h-5 w-2/5 rounded bg-[#e0e3e5]" />
                <div className="mt-3 h-4 w-4/5 rounded bg-[#eceef0]" />
              </article>
            ))}
          </section>
        )}

        {!loading && !error && insights.length === 0 && (
          <section className="mt-6 rounded-2xl border bg-white px-6 py-12 text-center text-sm text-[#5c5d64]">
            No insights are available for this period yet.
          </section>
        )}

        {!loading && !error && insights.length > 0 && (
          <section className="insights-grid mt-6" aria-live="polite">
            {insights.map((insight, index) => (
              <article key={`${insight.title}-${index}`} className={`insight-card ${insight.wide ? 'insight-card--wide' : ''}`}>
                <div className="flex justify-between gap-4">
                  <div className={`insight-icon insight-icon--${insight.tone}`}>
                    <Icon name={insight.icon} className="size-6" />
                  </div>
                  <span className={`insight-value insight-value--${insight.tone}`}>{insight.value}</span>
                </div>
                <h3 className="mt-5 text-xl font-semibold">{insight.title}</h3>
                <p className="mt-2 text-[15px] leading-6 text-[#5c5d64]">{insight.description}</p>
              </article>
            ))}
          </section>
        )}
      </main>
      <button type="button" aria-label="Ask Aura AI" className="ai-fab">
        <Icon name="sparkles" className="size-7 fill-current" />
      </button>
      <BottomNav active="insights" />
    </div>
  )
}
