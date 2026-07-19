import type { ReactNode } from 'react'

export type IconName = 'sparkles' | 'mail' | 'lock' | 'eye' | 'eyeOff' | 'bell' | 'trendDown' | 'coffee' | 'home' | 'card' | 'bag' | 'scan' | 'plus' | 'receipt' | 'chart' | 'car' | 'dots' | 'bulb' | 'check' | 'search' | 'cash' | 'flash' | 'gallery' | 'arrowUp' | 'calendar'

const paths: Record<IconName, ReactNode> = {
  sparkles: <path d="m12 3 1.3 4.2a5.2 5.2 0 0 0 3.5 3.5L21 12l-4.2 1.3a5.2 5.2 0 0 0-3.5 3.5L12 21l-1.3-4.2a5.2 5.2 0 0 0-3.5-3.5L3 12l4.2-1.3a5.2 5.2 0 0 0 3.5-3.5L12 3Z" />,
  mail: <path d="M4 6.5h16v11H4zM4.5 7l7.5 6 7.5-6" />, lock: <path d="M7 10h10v9H7zM9 10V7a3 3 0 0 1 6 0v3" />,
  eye: <><path d="M2.5 12s3.5-5 9.5-5 9.5 5 9.5 5-3.5 5-9.5 5-9.5-5-9.5-5Z" /><circle cx="12" cy="12" r="2.25" /></>, eyeOff: <><path d="M3 3l18 18M10.6 7.1A10 10 0 0 1 12 7c6 0 9.5 5 9.5 5a15 15 0 0 1-2.3 2.7M6.1 6.1A16 16 0 0 0 2.5 12s3.5 5 9.5 5a10 10 0 0 0 2-.2" /></>,
  bell: <><path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" /></>, trendDown: <path d="m5 7 5 5 4-4 5 5M19 9v4h-4" />,
  coffee: <><path d="M5 8h11v7a4 4 0 0 1-4 4H9a4 4 0 0 1-4-4V8ZM16 10h2a2 2 0 0 1 0 4h-2M8 3v2M12 3v2" /></>, home: <><path d="m3 11 9-8 9 8v10h-7v-6h-4v6H3V11Z" /></>,
  card: <><rect x="3" y="5" width="18" height="14" rx="2" /><path d="M3 10h18M7 15h3" /></>, bag: <><path d="M5 8h14l1 13H4L5 8ZM9 9V6a3 3 0 0 1 6 0v3" /></>,
  scan: <><path d="M4 8V4h4M16 4h4v4M20 16v4h-4M8 20H4v-4M8 9h8v6H8z" /></>, plus: <path d="M12 5v14M5 12h14" />,
  receipt: <><path d="M6 3h12v18l-3-2-3 2-3-2-3 2V3Z" /><path d="M9 8h6M9 12h6" /></>, chart: <><path d="M4 20V10M10 20V4M16 20v-7M22 20H2" /></>,
  car: <><path d="m5 11 2-5h10l2 5M4 11h16v7H4zM7 18v2M17 18v2M7.5 14h.01M16.5 14h.01" /></>, dots: <><circle cx="5" cy="12" r="1" fill="currentColor" stroke="none" /><circle cx="12" cy="12" r="1" fill="currentColor" stroke="none" /><circle cx="19" cy="12" r="1" fill="currentColor" stroke="none" /></>,
  bulb: <><path d="M9 18h6M10 22h4M8.5 15.5A7 7 0 1 1 15.5 15.5C14.5 16.3 14 17 14 18h-4c0-1-.5-1.7-1.5-2.5Z" /></>, check: <path d="m5 12 4 4L19 6" />,
  search: <><circle cx="11" cy="11" r="7" /><path d="m16 16 5 5" /></>, cash: <><rect x="3" y="6" width="18" height="12" rx="2" /><circle cx="12" cy="12" r="2.5" /></>,
  flash: <path d="m13 2-7 12h6l-1 8 7-12h-6l1-8Z" />, gallery: <><rect x="3" y="4" width="18" height="16" rx="2" /><circle cx="9" cy="9" r="2" /><path d="m21 15-5-5L5 20" /></>,
  arrowUp: <><path d="m6 14 5-5 4 4 4-5M19 8h-4" /></>, calendar: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M8 3v4M16 3v4M3 10h18" /></>,
}

export function Icon({ name, className = '' }: { name: IconName; className?: string }) {
  return <svg aria-hidden="true" className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>
}
