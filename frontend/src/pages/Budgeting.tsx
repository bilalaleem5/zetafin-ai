import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Target, PieChart, Save, RefreshCw } from 'lucide-react'
import api from '../api'

export default function Budgeting() {
  const [budgets, setBudgets] = useState<any[]>([])
  const [summary, setSummary] = useState<any>(null)
  const [categories, setCategories] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [newBudget, setNewBudget] = useState({ category: '', amount: '', month: new Date().toISOString().slice(0, 7) })

  const loadData = async () => {
    setLoading(true)
    try {
      const [bRes, sRes, cRes] = await Promise.all([
        api.get('/budgets'),
        api.get('/ai/ceo-summary'),
        api.get('/metadata/categories')
      ])
      setBudgets(bRes.data)
      setSummary(sRes.data)
      setCategories(cRes.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [])

  const handleSave = async () => {
    if (!newBudget.category || !newBudget.amount) return
    try {
      await api.post('/budgets', {
        ...newBudget,
        amount: parseFloat(newBudget.amount)
      })
      loadData()
      setNewBudget({ ...newBudget, amount: '' })
    } catch (err) {
      alert("Error saving budget")
    }
  }

  const currency = summary?.currency || 'PKR'

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Budget Management</h1>
          <p className="text-text-secondary text-sm">Set targets and monitor spending vs. actuals.</p>
        </div>
        <button onClick={loadData} className="btn-ghost text-sm py-2">
          <RefreshCw size={15} /> Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Set Budget Form */}
        <div className="card p-6 h-fit sticky top-24">
          <h3 className="font-semibold mb-6 flex items-center gap-2">
            <Target size={18} className="text-brand" /> Set Monthly Target
          </h3>
          <div className="space-y-4">
            <div>
              <label className="text-xs text-text-muted mb-1 block">Category</label>
              <select 
                className="input w-full"
                value={newBudget.category}
                onChange={e => setNewBudget({...newBudget, category: e.target.value})}
              >
                <option value="">Select Category...</option>
                {categories.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-text-muted mb-1 block">Amount ({currency})</label>
              <input 
                type="number" 
                className="input w-full" 
                placeholder="e.g. 50000"
                value={newBudget.amount}
                onChange={e => setNewBudget({...newBudget, amount: e.target.value})}
              />
            </div>
            <div>
              <label className="text-xs text-text-muted mb-1 block">Month</label>
              <input 
                type="month" 
                className="input w-full"
                value={newBudget.month}
                onChange={e => setNewBudget({...newBudget, month: e.target.value})}
              />
            </div>
            <button 
              onClick={handleSave}
              className="btn-primary w-full py-3 flex items-center justify-center gap-2"
            >
              <Save size={16} /> Save Budget
            </button>
          </div>
        </div>

        {/* Budget vs Actual Grid */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6">
            <h3 className="font-semibold mb-6 flex items-center gap-2">
              <PieChart size={18} className="text-brand" /> Performance Tracking
            </h3>
            
            {loading ? (
              <div className="space-y-4">
                {[1,2,3].map(i => <div key={i} className="h-16 bg-white/5 rounded-xl animate-pulse" />)}
              </div>
            ) : budgets.length === 0 ? (
              <p className="text-center text-text-muted py-12">No budgets set for this month yet.</p>
            ) : (
              <div className="space-y-8">
                {budgets.filter(b => b.month === newBudget.month).map((b, i) => {
                  const actual = summary?.actual_spending?.[b.category] || 0
                  const percent = Math.min((actual / b.amount) * 100, 100)
                  const isOver = actual > b.amount

                  return (
                    <motion.div 
                      key={b.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.1 }}
                      className="space-y-2"
                    >
                      <div className="flex justify-between items-end">
                        <div>
                          <span className="text-sm font-bold text-text-primary">{b.category}</span>
                          <p className="text-[10px] text-text-muted uppercase tracking-wider">
                            Actual: {actual.toLocaleString()} / Target: {b.amount.toLocaleString()}
                          </p>
                        </div>
                        <span className={`text-xs font-bold ${isOver ? 'text-red' : 'text-green'}`}>
                          {((actual / b.amount) * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                        <motion.div 
                          initial={{ width: 0 }}
                          animate={{ width: `${percent}%` }}
                          className={`h-full ${isOver ? 'bg-red' : 'bg-brand'}`}
                          style={{ boxShadow: isOver ? '0 0 10px rgba(244,63,94,0.3)' : '0 0 10px rgba(99,102,241,0.3)' }}
                        />
                      </div>
                      {isOver && (
                        <p className="text-[10px] text-red font-medium animate-pulse">
                          ⚠ Budget Exceeded by {(actual - b.amount).toLocaleString()} {currency}
                        </p>
                      )}
                    </motion.div>
                  )
                })}
              </div>
            )}
          </div>
          
          <div className="card p-6 bg-brand/5 border-brand/20">
            <h4 className="text-sm font-bold text-brand mb-2 uppercase tracking-widest">CEO Strategic Tip</h4>
            <p className="text-sm text-text-secondary leading-relaxed">
              ZetaFin AI analyzes these budgets to predict your runway. Keeping categories like "Miscellaneous" below 10% of total spend increases your financial stability score.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
