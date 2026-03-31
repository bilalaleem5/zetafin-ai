import { useEffect, useState } from 'react'
import { Download, TrendingUp, TrendingDown, DollarSign } from 'lucide-react'
import api from '../api'

interface PNLData {
  total_income: number
  total_expense: number
  net_profit: number
  income_breakdown: { category: string, amount: number }[]
  expense_breakdown: { category: string, amount: number }[]
}

export default function Reports() {
  const [data, setData] = useState<PNLData | null>(null)
  const [downloading, setDownloading] = useState(false)

  const load = async () => {
    try {
      const res = await api.get('/reports/pnl')
      setData(res.data)
    } catch {}
  }

  useEffect(() => { load() }, [])

  const exportCSV = async () => {
    setDownloading(true)
    try {
      const res = await api.get('/reports/export', { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'zetafin_ledger.csv')
      document.body.appendChild(link)
      link.click()
      link.parentNode?.removeChild(link)
    } catch {
      alert("Failed to export CSV.")
    } finally {
      setDownloading(false)
    }
  }

  if (!data) return <div className="p-12 text-center text-text-muted">Loading reports...</div>

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-20 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Financial Reports</h1>
          <p className="text-text-secondary text-sm mt-0.5">Profit & Loss statement and category breakdowns</p>
        </div>
        <button onClick={exportCSV} disabled={downloading} className="btn-primary flex items-center gap-2">
          <Download size={16} /> {downloading ? 'Exporting...' : 'Export CSV (Ledger)'}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card p-6 accent-left-green">
          <div className="flex items-center gap-2 mb-2 text-text-secondary font-medium"><TrendingUp size={16}/> Gross Revenue</div>
          <div className="text-3xl font-bold num text-green">PKR {data.total_income.toLocaleString()}</div>
        </div>
        <div className="card p-6 accent-left-red">
          <div className="flex items-center gap-2 mb-2 text-text-secondary font-medium"><TrendingDown size={16}/> Total Expenses</div>
          <div className="text-3xl font-bold num text-red">PKR {data.total_expense.toLocaleString()}</div>
        </div>
        <div className="card p-6 accent-left-brand">
          <div className="flex items-center gap-2 mb-2 text-text-secondary font-medium"><DollarSign size={16}/> Net Profit</div>
          <div className={`text-3xl font-bold num ${data.net_profit >= 0 ? 'text-brand' : 'text-red'}`}>PKR {data.net_profit.toLocaleString()}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card p-6 space-y-4">
          <h2 className="text-lg font-bold border-b border-white/5 pb-4">Revenue Breakdown</h2>
          <div className="space-y-3 pt-2">
            {data.income_breakdown.sort((a,b) => b.amount - a.amount).map((item, i) => (
              <div key={item.category} className="flex items-center justify-between group">
                <span className="font-medium text-text-secondary group-hover:text-white transition-colors">{i+1}. {item.category}</span>
                <span className="num font-bold text-green">PKR {item.amount.toLocaleString()}</span>
              </div>
            ))}
            {data.income_breakdown.length === 0 && <p className="text-text-muted text-sm py-4 italic">No income recorded.</p>}
          </div>
        </div>

        <div className="card p-6 space-y-4">
          <h2 className="text-lg font-bold border-b border-white/5 pb-4">Expense Breakdown</h2>
          <div className="space-y-3 pt-2">
            {data.expense_breakdown.sort((a,b) => b.amount - a.amount).map((item, i) => (
              <div key={item.category} className="flex items-center justify-between group">
                <span className="font-medium text-text-secondary group-hover:text-white transition-colors">{i+1}. {item.category}</span>
                <span className="num font-bold text-red">PKR {item.amount.toLocaleString()}</span>
              </div>
            ))}
            {data.expense_breakdown.length === 0 && <p className="text-text-muted text-sm py-4 italic">No expenses recorded.</p>}
          </div>
        </div>
      </div>
    </div>
  )
}
