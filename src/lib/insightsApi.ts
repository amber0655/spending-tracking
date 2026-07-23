import type { IconName } from '../components/Icon'
import { auth } from './firebase'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'

export type InsightInterval = 'weekly' | 'monthly' | 'yearly'
export type InsightTone = 'good' | 'alert' | 'neutral'

export type Insight = {
  icon: IconName
  title: string
  value: string
  tone: InsightTone
  description: string
  wide: boolean
}

async function responseError(response: Response) {
  try {
    const body = await response.json() as { detail?: string }
    return body.detail || `Unable to load insights (${response.status})`
  } catch {
    return `Unable to load insights (${response.status})`
  }
}

export async function getInsights(interval: InsightInterval, signal?: AbortSignal): Promise<Insight[]> {
  const user = auth.currentUser
  if (!user) throw new Error('You must be signed in to view insights.')

  const request = async (forceRefresh = false) => {
    const token = await user.getIdToken(forceRefresh)
    const params = new URLSearchParams({ interval })
    return fetch(`${API_BASE_URL}/insights?${params}`, {
      signal,
      headers: { Authorization: `Bearer ${token}` },
    })
  }

  let response = await request()
  if (response.status === 401) response = await request(true)
  if (!response.ok) throw new Error(await responseError(response))
  return response.json() as Promise<Insight[]>
}

