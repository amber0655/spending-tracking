import { auth } from './firebase'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'

export type ReceiptScanResult = {
  merchant: string
  amount: string
  date: string
  rawText?: string
}

async function errorMessage(response: Response) {
  try {
    const body = await response.json() as { detail?: string }
    return body.detail || `Receipt scan failed (${response.status})`
  } catch {
    return `Receipt scan failed (${response.status})`
  }
}

export async function scanReceipt(file: File): Promise<ReceiptScanResult> {
  const user = auth.currentUser
  if (!user) throw new Error('You must be signed in to scan a receipt.')

  const request = async (forceRefresh = false) => {
    const token = await user.getIdToken(forceRefresh)
    const formData = new FormData()
    formData.append('file', file, file.name || 'receipt.jpg')
    return fetch(`${API_BASE_URL}/receipts/scan`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    })
  }

  let response = await request()
  if (response.status === 401) response = await request(true)
  if (!response.ok) throw new Error(await errorMessage(response))

  const result = await response.json() as Partial<ReceiptScanResult> & { amount?: string | number; raw_text?: string }
  const amount = result.amount == null ? '' : String(result.amount)
  return {
    merchant: typeof result.merchant === 'string' ? result.merchant : '',
    amount: amount.match(/\d[\d,]*\.\d{2}/)?.[0].replace(/,/g, '') ?? '',
    date: typeof result.date === 'string' ? result.date : '',
    rawText: result.rawText ?? result.raw_text,
  }
}
