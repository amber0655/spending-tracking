import { Navigate, Route, Routes } from 'react-router-dom'
import { DashboardPage } from './pages/DashboardPage'
import { InsightsPage } from './pages/InsightsPage'
import { LoginPage } from './pages/LoginPage'
import { ManualExpensePage } from './pages/ManualExpensePage'
import { ReceiptScanPage } from './pages/ReceiptScanPage'
import { TransactionsPage } from './pages/TransactionsPage'
import { RequireAuth } from './auth/RequireAuth'
import { AccountPage } from './pages/AccountPage'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/dashboard" element={<RequireAuth><DashboardPage /></RequireAuth>} />
      <Route path="/expenses/new" element={<RequireAuth><ManualExpensePage /></RequireAuth>} />
      <Route path="/transactions" element={<RequireAuth><TransactionsPage /></RequireAuth>} />
      <Route path="/insights" element={<RequireAuth><InsightsPage /></RequireAuth>} />
      <Route path="/receipts/scan" element={<RequireAuth><ReceiptScanPage /></RequireAuth>} />
      <Route path="/account" element={<RequireAuth><AccountPage /></RequireAuth>} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}
