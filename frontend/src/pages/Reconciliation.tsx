import React, { useState } from 'react'
import { UploadCloud, CheckCircle2, FileText, ArrowRight, X } from 'lucide-react'
import api from '../api'

interface BankTx {
  id: number
  date: string
  description: string
  amount: number
}

export default function Reconciliation() {
  const [file, setFile] = useState<File | null>(null)
  const [parsing, setParsing] = useState(false)
  const [bankTxs, setBankTxs] = useState<BankTx[]>([])
  const [importedIds, setImportedIds] = useState<number[]>([])

  const [showModal, setShowModal] = useState(false)
  const [activeTx, setActiveTx] = useState<BankTx | null>(null)
  const [form, setForm] = useState({ category: 'Client Revenue', description: '', type: 'income', tax_amount: '0', tax_type: '' })
  const [categories, setCategories] = useState<string[]>(['Software', 'Hardware', 'Marketing', 'Office Supplies', 'Legal', 'Contractor', 'Rent', 'Salaries', 'Utilities', 'Operations', 'Travel', 'Miscellaneous', 'Client Revenue'])
  const [customCat, setCustomCat] = useState('')
  const [saving, setSaving] = useState(false)

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0])
    }
  }

  const uploadAndParse = async () => {
    if (!file) return
    setParsing(true)
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      const { data } = await api.post('/reconciliation/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setBankTxs(data.transactions)
      const { data: cats } = await api.get('/metadata/categories')
      setCategories(cats)
    } catch (err) {
      alert('Failed to parse bank statement. Ensure it is a valid CSV.')
    } finally {
      setParsing(false)
    }
  }

  const openImport = (tx: BankTx) => {
    setActiveTx(tx)
    setForm({
      category: tx.amount > 0 ? 'Client Revenue' : 'Rent',
      description: tx.description,
      type: tx.amount > 0 ? 'income' : 'expense',
      tax_amount: '0',
      tax_type: ''
    })
    setShowModal(true)
  }

  const handleImport = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!activeTx) return
    setSaving(true)
    const finalCat = form.category === 'Other' ? customCat : form.category
    try {
      const payload = {
        amount: Math.abs(activeTx.amount),
        tax_amount: parseFloat(form.tax_amount) || 0,
        tax_type: form.tax_type,
        category: finalCat,
        description: form.description,
        type: form.type,
        date: new Date(activeTx.date).toISOString() || new Date().toISOString()
      }
      await api.post('/transactions/', payload)
      setImportedIds([...importedIds, activeTx.id])
      setShowModal(false); setCustomCat('')
    } catch {
      alert('Error importing transaction')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-20">
      <div>
        <h1 className="text-2xl font-bold">Bank Reconciliation</h1>
        <p className="text-text-secondary text-sm mt-0.5">Upload a CSV bank statement to sync your ZetaFin records.</p>
      </div>

      {bankTxs.length === 0 ? (
        <div className="card p-12 flex flex-col items-center justify-center text-center border-dashed border-2 border-white/10 mt-6">
          <div className="w-16 h-16 rounded-2xl bg-brand/10 text-brand flex items-center justify-center mb-6">
            <UploadCloud size={32} />
          </div>
          <h2 className="text-xl font-bold mb-2">Upload CSV Statement</h2>
          <p className="text-text-muted text-sm max-w-md mb-8">
            Select an exported CSV from Meezan, HBL, Standard Chartered, or Nayapay. Our AI parser will extract the transactions automatically.
          </p>
          <div className="flex gap-4 items-center">
            <input type="file" accept=".csv" onChange={handleFile} className="text-sm file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-brand/10 file:text-brand hover:file:bg-brand/20" />
            <button disabled={!file || parsing} onClick={uploadAndParse} className="btn-primary py-2 px-6">
              {parsing ? 'Parsing...' : 'Analyze CSV'}
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex justify-between items-center mb-6">
            <p className="text-lg font-bold">Found {bankTxs.length} Transactions</p>
            <button onClick={() => { setBankTxs([]); setFile(null) }} className="btn-ghost text-xs">Upload New File</button>
          </div>

          <div className="card overflow-hidden">
            <div className="divide-y divide-border">
              {bankTxs.map((tx) => {
                const isImported = importedIds.includes(tx.id)
                return (
                  <div key={tx.id} className={`p-4 flex items-center gap-4 hover:bg-white/5 transition-colors ${isImported ? 'opacity-50' : ''}`}>
                    <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center text-text-muted flex-shrink-0">
                      <FileText size={18} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold truncate text-sm">{tx.description}</p>
                      <p className="text-xs text-text-muted">{tx.date}</p>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <p className={`font-bold num ${tx.amount > 0 ? 'text-green' : 'text-red'}`}>
                        {tx.amount > 0 ? '+' : ''}PKR {Math.abs(tx.amount).toLocaleString()}
                      </p>
                    </div>
                    <div className="pl-4 border-l border-white/10 flex-shrink-0 ml-2">
                      {isImported ? (
                        <div className="flex items-center gap-1.5 text-brand text-xs font-bold px-3 py-1.5 bg-brand/10 rounded-lg">
                          <CheckCircle2 size={14} /> Synced
                        </div>
                      ) : (
                        <button onClick={() => openImport(tx)} className="flex items-center gap-1.5 bg-white text-black font-bold text-xs px-4 py-2 rounded-lg hover:bg-gray-200 transition-colors">
                          Import <ArrowRight size={14} />
                        </button>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {showModal && activeTx && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="glass w-full max-w-sm p-8 space-y-6 relative rounded-2xl">
            <button onClick={() => setShowModal(false)} className="absolute top-4 right-4 p-2 hover:bg-white/10 rounded-xl"><X size={20}/></button>
            
            <div>
              <h2 className="text-lg font-bold mb-1">Import to ZetaFin</h2>
              <p className="text-xs text-brand truncate max-w-[280px]">{activeTx.description}</p>
            </div>

            <div className="p-4 bg-white/5 rounded-xl flex justify-between items-center border border-white/10">
              <span className="text-text-muted text-xs uppercase font-bold tracking-wider">Bank Amount</span>
              <span className={`text-lg font-bold num ${activeTx.amount > 0 ? 'text-green' : 'text-red'}`}>
                {activeTx.amount > 0 ? '+' : '-'} PKR {Math.abs(activeTx.amount).toLocaleString()}
              </span>
            </div>

            <form onSubmit={handleImport} className="space-y-4">
              <div className="input-group">
                <label className="input-label">Transaction Type</label>
                <div className="grid grid-cols-2 gap-2 p-1 bg-bg-surface rounded-xl">
                  {['income', 'expense'].map((t) => (
                    <button
                      key={t} type="button"
                      onClick={() => setForm({ ...form, type: t, category: t === 'income' ? 'Client Revenue' : 'Office Supplies' })}
                      className={`py-2 rounded-lg text-xs font-bold capitalize transition-all ${
                        form.type === t ? (t === 'income' ? 'bg-green text-white' : 'bg-red text-white') : 'text-text-secondary hover:text-text-primary'
                      }`}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>

              <div className="input-group">
                <label className="input-label">Categorize As</label>
                <select className="input" value={form.category} onChange={e => setForm({...form, category: e.target.value})}>
                  {categories.filter(c => form.type === 'income' ? (c.includes('Revenue') || c === 'Other') : !c.includes('Revenue')).map(c => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                  <option value="Other">Other (Custom)</option>
                </select>
              </div>
              {(form.category === 'Other' || form.category === 'Other (Custom)') && (
                <div className="input-group animate-in fade-in slide-in-from-top-2">
                  <label className="input-label">Custom Category Name</label>
                  <input className="input" placeholder="e.g. Photography" value={customCat} onChange={(e) => setCustomCat(e.target.value)} required />
                </div>
              )}

              <div className="input-group">
                <label className="input-label">Refined Description</label>
                <input className="input" value={form.description} onChange={e => setForm({...form, description: e.target.value})} required />
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
                  </select>
                </div>
              </div>

              <button type="submit" disabled={saving} className="btn-primary w-full py-3.5 shadow-xl shadow-brand/20 mt-4 font-bold text-sm">
                {saving ? 'Syncing...' : 'Sync Transaction'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
