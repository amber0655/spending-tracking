import { Icon, type IconName } from './Icon'

export type Transaction = { icon: IconName; merchant: string; meta: string; amount: string; kind: string; income?: boolean; date?: string }

export function TransactionRow({ transaction }: { transaction: Transaction }) {
  return <div className="transaction-row"><div className={`transaction-icon ${transaction.income ? 'transaction-icon--income' : ''}`}><Icon name={transaction.icon} className="size-5" /></div><div className="min-w-0 flex-1"><h3 className="truncate text-[15px] font-medium text-[#191c1e] sm:text-base">{transaction.merchant}</h3><p className="mt-0.5 truncate text-sm text-[#67686f]">{transaction.meta}</p></div><div className="shrink-0 text-right"><p className={`font-mono text-[15px] font-medium sm:text-base ${transaction.income ? 'text-[#00714d]' : 'text-[#191c1e]'}`}>{transaction.amount}</p><p className={`mt-0.5 text-[10px] uppercase tracking-wide ${transaction.income ? 'text-[#00714d]' : 'text-[#67686f]'}`}>{transaction.kind}</p></div></div>
}
