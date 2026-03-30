import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Plus, Receipt, Repeat, Trash2, X, Edit2, Users, History } from 'lucide-react'
import api from '../api'

interface Recurring { id: number; title: string; amount: number; category: string; frequency: string; next_due_date: string; is_active: boolean }
interface Transaction { id: number; amount: number; category: string; description: string; date: string; type: string }
interface Employee { id: number; name: string; role: string; salary: number }

export default function Expenses() {
  const [recurring, setRecurring] = useState<Recurring[]>([])
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [employees, setEmployees] = useState<Employee[]>([])
  
  const [showManual, setShowManual] = useState(false)
  const [showRecur, setShowRecur] = useState(false)
  const [editItem, setEditItem] = useState<{ type: 'recur' | 'manual', data: any } | null>(null)
  
  const [manualForm, setManualForm] = useState({ amount: '', category: 'Marketing', description: '' })
  const [recurForm, setRecurForm] = useState({ title: '', amount: '', category: 'Rent', frequency: 'monthly', next_due_date: '' })

  const load = async () => {
    try {
      const [recRes, txRes, empRes] = await Promise.all([
        api.get('/recurring-expenses'),
        api.get('/transactions/'),
        api.get('/employees/')
      ])
      setRecurring(recRes.data)
      setTransactions(txRes.data.filter((t: any) => t.type === 'expense'))
      setEmployees(empRes.data)
    } catch {}
  }

  useEffect(() => { load() }, [])

  const handleManual = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editItem?.type === 'manual') {
        await api.patch(`/transactions/${editItem.data.id}`, { ...manualForm, amount: parseFloat(manualForm.amount), type: 'expense' })
      } else {
        await api.post('/transactions/', { ...manualForm, amount: parseFloat(manualForm.amount), type: 'expense' })
      }
      setShowManual(false); setEditItem(null); setManualForm({ amount: '', category: 'Marketing', description: '' })
      load()
    } catch { alert('Error saving expense') }
  }

  const handleRecur = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editItem?.type === 'recur') {
        await api.patch(`/recurring-expenses/${editItem.data.id}`, { ...recurForm, amount: parseFloat(recurForm.amount) })
      } else {
        await api.post('/recurring-expenses', { ...recurForm, amount: parseFloat(recurForm.amount) })
      }
      setShowRecur(false); setEditItem(null); setRecurForm({ title: '', amount: '', category: 'Rent', frequency: 'monthly', next_due_date: '' })
      load()
    } catch { alert('Error saving recurring expense') }
  }

  const handleDelete = async (type: 'recur' | 'manual', id: number) => {
    if (!confirm('Are you sure you want to delete this?')) return
    try {
      const url = type === 'recur' ? `/recurring-expenses/${id}` : `/transactions/${id}`
      await api.delete(url)
      load()
    } catch { alert('Error deleting item') }
  }

  const openEdit = (type: 'recur' | 'manual', item: any) => {
    setEditItem({ type, data: item })
    if (type === 'manual') {
      setManualForm({ amount: item.amount.toString(), category: item.category, description: item.description })
      setShowManual(true)
    } else {
      setRecurForm({ title: item.title, amount: item.amount.toString(), category: item.category, frequency: item.frequency, next_due_date: item.next_due_date.split('T')[0] })
      setShowRecur(true)
    }
  }

  const totalMonthlyBurn = recurring.reduce((a, r) => a + (r.frequency === 'monthly' ? r.amount : r.amount * 4), 0) + 
                           employees.reduce((a, e) => a + e.salary, 0)

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-20">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Expenses & Burn</h1>
          <p className="text-text-secondary text-sm mt-0.5">
            Total Monthly Estimated Burn: <span className="num font-bold text-brand ml-1">PKR {totalMonthlyBurn.toLocaleString()}</span>
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => { setEditItem(null); setManualForm({ amount: '', category: 'Marketing', description: '' }); setShowManual(true) }} className="btn-primary-outline">
            <Plus size={18} /> Log Manual
          </button>
          <button onClick={() => { setEditItem(null); setRecurForm({ title: '', amount: '', category: 'Rent', frequency: 'monthly', next_due_date: '' }); setShowRecur(true) }} className="btn-primary">
            <Repeat size={18} /> Add Recurring
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          {/* Recurring Section */}
          <section className="space-y-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Repeat size={20} className="text-brand" /> Monthly Recurring
            </h2>
            {recurring.length === 0 ? (
              <div className="card p-8 text-center text-text-muted italic text-sm">No automated costs setup.</div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {recurring.map(r => (
                  <div key={r.id} className="card p-5 group relative">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <p className="font-bold text-lg">{r.title}</p>
                        <p className="text-xs text-text-muted">{r.category} · {r.frequency}</p>
                      </div>
                      <div className="num font-bold text-brand">PKR {r.amount.toLocaleString()}</div>
                    </div>
                    <div className="flex justify-between items-center mt-4">
                      <span className="text-[10px] text-text-muted uppercase font-medium">Due: {new Date(r.next_due_date).toLocaleDateString()}</span>
                      <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button onClick={() => openEdit('recur', r)} className="p-1.5 hover:bg-white/10 rounded-lg text-text-muted"><Edit2 size={14}/></button>
                        <button onClick={() => handleDelete('recur', r.id)} className="p-1.5 hover:bg-white/10 rounded-lg text-red/70"><Trash2 size={14}/></button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* History Section */}
          <section className="space-y-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <History size={20} className="text-amber" /> Manual Expense History
            </h2>
            <div className="card overflow-hidden">
              <table className="w-full text-left">
                <thead className="bg-white/5 border-b border-white/5">
                  <tr>
                    <th className="p-4 text-xs font-semibold text-text-muted uppercase tracking-wider">Date</th>
                    <th className="p-4 text-xs font-semibold text-text-muted uppercase tracking-wider">Description</th>
                    <th className="p-4 text-xs font-semibold text-text-muted uppercase tracking-wider text-right">Amount</th>
                    <th className="p-4 w-20"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {transactions.length === 0 ? (
                    <tr><td colSpan={4} className="p-12 text-center text-text-muted italic text-sm">No manual logs yet.</td></tr>
                  ) : (
                    transactions.map(t => (
                      <tr key={t.id} className="group hover:bg-white/5 transition-colors">
                        <td className="p-4 text-sm text-text-muted">{new Date(t.date).toLocaleDateString()}</td>
                        <td className="p-4">
                          <p className="font-medium text-sm">{t.description}</p>
                          <p className="text-[10px] text-text-muted uppercase">{t.category}</p>
                        </td>
                        <td className="p-4 text-right font-bold text-red/80 num text-sm">PKR {t.amount.toLocaleString()}</td>
                        <td className="p-4">
                          <div className="flex gap-2 opacity-0 group-hover:opacity-100 justify-end transition-opacity">
                            <button onClick={() => openEdit('manual', t)} className="text-text-muted p-1 hover:text-white"><Edit2 size={14}/></button>
                            <button onClick={() => handleDelete('manual', t.id)} className="text-red/60 p-1 hover:text-red"><Trash2 size={14}/></button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </div>

        <div className="space-y-6">
          {/* Salaries Overview */}
          <section className="space-y-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Users size={20} className="text-brand" /> Team Salaries
            </h2>
            <div className="card p-5 space-y-4 bg-brand/5 border-brand/20">
              {employees.length === 0 ? (
                <p className="text-xs text-text-muted italic text-center py-4">No team members added.</p>
              ) : (
                <div className="space-y-3">
                  {employees.map(e => (
                    <div key={e.id} className="flex justify-between items-center text-sm border-b border-white/5 pb-2">
                      <div>
                        <p className="font-medium">{e.name}</p>
                        <p className="text-[10px] text-text-muted uppercase">{e.role}</p>
                      </div>
                      <span className="num font-bold">PKR {e.salary.toLocaleString()}</span>
                    </div>
                  ))}
                  <div className="flex justify-between items-center pt-2 font-bold text-brand">
                    <span>Monthly Total</span>
                    <span className="num text-lg">PKR {employees.reduce((a, e) => a + e.salary, 0).toLocaleString()}</span>
                  </div>
                </div>
              )}
            </div>
          </section>

          <section className="space-y-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Receipt size={20} className="text-emerald" /> Quick Categories
            </h2>
            <div className="card p-5 space-y-2">
              {['Marketing', 'Software', 'Rent', 'Utilities', 'Travel', 'Vendor'].map(c => (
                <div key={c} className="flex justify-between items-center p-2 hover:bg-white/5 rounded-lg text-sm text-text-secondary">
                  <span>{c}</span>
                  <span className="text-[10px] bg-white/5 px-2 py-1 rounded text-text-muted font-medium uppercase">Active</span>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>

      {/* Manual Modals - Combined Logic */}
      {showManual && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="glass w-full max-w-md p-8 space-y-6 shadow-2xl border-white/10">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold">{editItem ? 'Edit Expense' : 'Log Manual Expense'}</h2>
              <button onClick={() => { setShowManual(false); setEditItem(null); }} className="hover:rotate-90 transition-transform"><X /></button>
            </div>
            <form onSubmit={handleManual} className="space-y-5">
              <div className="input-group">
                <label className="input-label">Amount (PKR)</label>
                <input className="input" type="number" value={manualForm.amount} onChange={e => setManualForm({...manualForm, amount: e.target.value})} required />
              </div>
              <div className="input-group">
                <label className="input-label">Category</label>
                <select className="input" value={manualForm.category} onChange={e => setManualForm({...manualForm, category: e.target.value})}>
                  {['Marketing', 'Software', 'Rent', 'Utilities', 'Travel', 'Vendor', 'Other'].map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div className="input-group">
                <label className="input-label">Description</label>
                <input className="input" placeholder="Facebook Ads - March" value={manualForm.description} onChange={e => setManualForm({...manualForm, description: e.target.value})} required />
              </div>
              <button type="submit" className="btn-primary w-full py-3.5 shadow-xl shadow-brand/20 font-bold tracking-wide">
                {editItem ? 'Update Expense' : 'Log Expense'}
              </button>
            </form>
          </motion.div>
        </div>
      )}

      {/* Recurring Modal */}
      {showRecur && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="glass w-full max-w-md p-8 space-y-6 shadow-2xl border-white/10">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold">{editItem ? 'Edit Recurring' : 'Setup Recurring Cost'}</h2>
              <button onClick={() => { setShowRecur(false); setEditItem(null); }} className="hover:rotate-90 transition-transform"><X /></button>
            </div>
            <form onSubmit={handleRecur} className="space-y-5">
              <div className="input-group">
                <label className="input-label">Title</label>
                <input className="input" placeholder="Office Rent" value={recurForm.title} onChange={e => setRecurForm({...recurForm, title: e.target.value})} required />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="input-group">
                  <label className="input-label">Amount (PKR)</label>
                  <input className="input" type="number" value={recurForm.amount} onChange={e => setRecurForm({...recurForm, amount: e.target.value})} required />
                </div>
                <div className="input-group">
                  <label className="input-label">Frequency</label>
                  <select className="input" value={recurForm.frequency} onChange={e => setRecurForm({...recurForm, frequency: e.target.value})}>
                    <option value="monthly">Monthly</option>
                    <option value="weekly">Weekly</option>
                  </select>
                </div>
              </div>
              <div className="input-group">
                <label className="input-label">Category</label>
                <select className="input" value={recurForm.category} onChange={e => setRecurForm({...recurForm, category: e.target.value})}>
                  {['Marketing', 'Software', 'Rent', 'Utilities', 'Travel', 'Vendor'].map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div className="input-group">
                <label className="input-label">Next Due Date</label>
                <input className="input" type="date" value={recurForm.next_due_date} onChange={e => setRecurForm({...recurForm, next_due_date: e.target.value})} required />
              </div>
              <button type="submit" className="btn-primary w-full py-3.5 shadow-xl shadow-brand/20 font-bold tracking-wide">
                {editItem ? 'Update Recurring' : 'Save Recurring Cost'}
              </button>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  )
}
