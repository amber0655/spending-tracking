import { NavLink } from 'react-router-dom'
import { Icon, type IconName } from './Icon'

export type NavKey = 'home' | 'expense' | 'transactions' | 'insights'

export function AppHeader() {
  return (
    <header className="app-header">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5 sm:px-8">
        <h1 className="text-2xl font-semibold tracking-[-0.02em] text-black sm:text-[28px]">
          Aura Finance
        </h1>
        <button type="button" aria-label="Notifications" className="icon-button">
          <Icon name="bell" className="size-6" />
        </button>
      </div>
    </header>
  )
}

export function BottomNav({ active }: { active: NavKey }) {
  const items: Array<{ icon: IconName; label: string; key: NavKey; path: string }> = [
    { icon: 'home', label: 'Home', key: 'home', path: '/dashboard' },
    { icon: 'plus', label: 'Add Expense', key: 'expense', path: '/expenses/new' },
    { icon: 'receipt', label: 'Transactions', key: 'transactions', path: '/transactions' },
    { icon: 'chart', label: 'Insights', key: 'insights', path: '/insights' },
  ]

  return (
    <nav aria-label="Primary navigation" className="bottom-nav">
      {items.map((item) => (
        <NavLink
          key={item.key}
          to={item.path}
          aria-current={item.key === active ? 'page' : undefined}
          className={`nav-item ${item.key === active ? 'nav-item--active' : ''}`}
        >
          <Icon name={item.icon} className="size-5" />
          <span>{item.label}</span>
        </NavLink>
      ))}
    </nav>
  )
}
