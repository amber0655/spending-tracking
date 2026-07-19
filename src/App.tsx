import { Navigate, Route, Routes } from 'react-router-dom'
import { DashboardPage } from './pages/DashboardPage'
import { InsightsPage } from './pages/InsightsPage'
import { LoginPage } from './pages/LoginPage'
import { ManualExpensePage } from './pages/ManualExpensePage'
import { ReceiptScanPage } from './pages/ReceiptScanPage'
import { TransactionsPage } from './pages/TransactionsPage'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/expenses/new" element={<ManualExpensePage />} />
      <Route path="/transactions" element={<TransactionsPage />} />
      <Route path="/insights" element={<InsightsPage />} />
      <Route path="/receipts/scan" element={<ReceiptScanPage />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}
