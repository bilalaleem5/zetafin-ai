import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Plus, TrendingUp, TrendingDown, Search, X } from 'lucide-react'
import api from '../api'

interface Tx {
  id: number; amount: number; category: string;
  description: string; type: string; date: string;
  tax_amount: number; tax_type: string;
}

const INCOME_CATS = ['Client Revenue', 'Project Work', 'Retainer', 'Other']
const EXPENSE_CATS = ['Rent', 'Salaries', 'Marketing', 'Utilities', 'Operations', 'Travel', 'Miscellaneous']

export default function Transactions() {
  const [txs, setTxs]         = useState<Tx[]>([])
  const [loading, setLoading] = useState(true)
  const [q, setQ]             = useState('')
  const [showModal, setShowModal] = useState(false)
  const [form, setForm]       = useState({ amount: '', tax_amount: '0', tax_type: '', category: 'Client Revenue', description: '', type: 'income' })
  const [saving, setSaving]   = useState(false)

  const load = async () => {
    setLoading(true)
    try { const { data } = await api.get('/transactions/'); setTxs(data) }
    catch { /* demo */ }
    finally { setLoading(false) }
  }
  useEffect(() => { load() }, [])

  const save = async (e: React.FormEvent) => {
    e.preventDefault(); setSaving(true)
    try {
      const payload = { 
        ...form, 
        amount: parseFloat(form.amount), 
        tax_amount: form.tax_amount ? parseFloat(form.tax_amount) : 0,
        date: new Date().toISOString() 
      }
      await api.post('/transactions/', payload)
      setShowModal(false); setForm({ amount: '', tax_amount: '0', tax_type: '', category: 'Client Revenue', description: '', type: 'income' })
      load()
    } catch { /* ignore */ }
    finally { setSaving(false) }
  }

  const filtered = txs.filter(t =>
    t.description.toLowerCase().includes(q.toLowerCase()) ||
    t.category.toLowerCase().includes(q.toLowerCase())
  )
  const totalIn  = txs.filter(t => t.type === 'income').reduce((a, t) => a + t.amount, 0)
  const totalOut = txs.filter(t => t.type === 'expense').reduce((a, t) => a + t.amount, 0)

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Transactions</h1>
          <p className="text-text-secondary text-sm mt-0.5">All income and expenses</p>
        </div>
        <button id="add-tx-btn" onClick={() => setShowModal(true)} className="btn-primary">
          <Plus size={18} /> Add Entry
        </button>
      </div>

      {/* Summary Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { label: 'Total Income',  value: totalIn,          color: 'text-green',  accent: 'accent-left-green' },
          { label: 'Total Expenses',value: totalOut,         color: 'text-red',    accent: 'accent-left-red' },
          { label: 'Net Profit',    value: totalIn - totalOut, color: totalIn - totalOut >= 0 ? 'text-green' : 'text-red', accent: 'accent-left-brand' },
        ].map((s) => (
          <div key={s.label} className={`card p-5 ${s.accent}`}>
            <p className="text-text-secondary text-xs font-medium mb-1">{s.label}</p>
            <p className={`num text-2xl font-bold ${s.color}`}>PKR {s.value.toLocaleString()}</p>
          </div>
        ))}
      </div>

      {/* Search */}
      <div className="relative">
        <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted" />
        <input
          className="input pl-11 py-2.5"
          placeholder="Search by description or category…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>

      {/* List */}
      <div className="card overflow-hidden">
        {loading ? (
          <div className="p-6 space-y-3">
            {[1, 2, 3].map((i) => <div key={i} className="shimmer h-16 rounded-xl" />)}
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-20 text-center text-text-muted">
            <TrendingUp size={40} className="mx-auto mb-3 opacity-20" />
            <p>No transactions yet. Add your first one!</p>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {filtered.map((t, i) => (
              <motion.div
                key={t.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.03 }}
                className="flex items-center gap-4 px-6 py-4 hover:bg-white/2 transition-colors"
              >
                <div className={`p-2.5 rounded-xl flex-shrink-0 ${t.type === 'income' ? 'bg-green/10' : 'bg-red/10'}`}>
                  {t.type === 'income'
                    ? <TrendingUp size={18} className="text-green" />
                    : <TrendingDown size={18} className="text-red" />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{t.description}</p>
                  <p className="text-xs text-text-muted">{new Date(t.date).toLocaleDateString('en-PK', { day: 'numeric', month: 'short', year: 'numeric' })} · {t.category}</p>
                </div>
                <span className={`num font-bold flex-shrink-0 text-right ${t.type === 'income' ? 'text-green' : 'text-red'}`}>
                  {t.type === 'income' ? '+' : '-'}PKR {t.amount.toLocaleString()}
                  {t.tax_amount > 0 && <span className="block text-[9px] text-text-muted font-normal mt-0.5 opacity-60">incl. {t.tax_type} Tax {t.tax_amount.toLocaleString()}</span>}
                </span>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Add Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            className="glass w-full max-w-md p-8 space-y-6"
          >
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold">New Transaction</h2>
              <button onClick={() => setShowModal(false)} className="p-1.5 hover:bg-white/10 rounded-lg transition-colors">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={save} className="space-y-4">
              {/* Type toggle */}
              <div className="grid grid-cols-2 gap-2 p-1 bg-bg-surface rounded-xl">
                {['income', 'expense'].map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setForm({ ...form, type: t, category: t === 'income' ? 'Client Revenue' : 'Rent' })}
                    className={`py-2 rounded-lg text-sm font-semibold capitalize transition-all ${
                      form.type === t
                        ? t === 'income' ? 'bg-green text-white' : 'bg-red text-white'
                        : 'text-text-secondary hover:text-text-primary'
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>
              <div className="input-group">
                <label className="input-label">Net Amount (PKR) <span className="text-[10px] text-text-muted ml-0.5 normal-case tracking-normal">(Actual bank effect)</span></label>
                <input className="input" type="number" placeholder="150000" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} required />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="input-group">
                  <label className="input-label">Tax Withheld</label>
                  <input className="input" type="number" placeholder="0" value={form.tax_amount} onChange={e => setForm({...form, tax_amount: e.target.value})} />
                </div>
                <div className="input-group">
                  <label className="input-label">Tax Type</label>
                  <select className="input" value={form.tax_type} onChange={e => setForm({...form, tax_type: e.target.value})}>
                    <option value="">None</option>
                    <option value="WHT">WHT</option>
                    <option value="GST">GST</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>
              <div className="input-group">
                <label className="input-label">Category</label>
                <select className="input" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
                  {(form.type === 'income' ? INCOME_CATS : EXPENSE_CATS).map((c) => <option key={c}>{c}</option>)}
                </select>
              </div>
              <div className="input-group">
                <label className="input-label">Description</label>
                <input className="input" placeholder="Ali Traders — March Invoice" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} required />
              </div>
              <button type="submit" disabled={saving} className="btn-primary w-full py-3">
                {saving ? 'Saving…' : 'Save Transaction'}
              </button>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  )
}
