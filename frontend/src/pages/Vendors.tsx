import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Plus, Store, CheckCircle2, Clock, AlertTriangle, X, Edit2, Trash2, Building2 } from 'lucide-react'
import api from '../api'

interface VendorBill { id: number; title: string; amount: number; due_date: string; status: string; tax_amount: number; tax_type: string; }
interface Vendor { id: number; name: string; category: string; contact: string; status: string }

const statusStyle: Record<string, string> = {
  Paid:    'badge-green',
  Pending: 'badge-amber',
  Overdue: 'badge-red',
  Partial: 'badge-brand',
}
const statusIcon: Record<string, any> = {
  Paid: CheckCircle2, Pending: Clock, Overdue: AlertTriangle, Partial: Clock,
}

export default function Vendors() {
  const [vendors, setVendors] = useState<Vendor[]>([])
  const [showModal, setShowModal] = useState(false)
  const [showBillModal, setShowBillModal] = useState(false)
  const [selectedVendor, setSelectedVendor] = useState<Vendor | null>(null)
  const [editVendor, setEditVendor] = useState<Vendor | null>(null)
  const [editBill, setEditBill] = useState<VendorBill | null>(null)
  
  const [bills, setBills] = useState<VendorBill[]>([])
  const [form, setForm] = useState({ name: '', category: 'Software', contact: '' })
  const [bForm, setBForm] = useState({ title: '', amount: '', tax_amount: '0', tax_type: '', due_date: '' })
  const [saving, setSaving] = useState(false)

  const load = async () => {
    try { const { data } = await api.get('/vendors/'); setVendors(data) } catch {}
  }
  useEffect(() => { load() }, [])

  const save = async (e: React.FormEvent) => {
    e.preventDefault(); setSaving(true)
    try {
      if (editVendor) {
        await api.patch(`/vendors/${editVendor.id}`, form)
      } else {
        await api.post('/vendors/', form)
      }
      setShowModal(false); setEditVendor(null); setForm({ name: '', category: 'Software', contact: '' })
      load()
    } catch { alert('Error saving vendor') } finally { setSaving(false) }
  }

  const handleDeleteVendor = async (id: number) => {
    if (!confirm('Are you sure? This will delete the vendor and all their bills.')) return
    try {
      await api.delete(`/vendors/${id}`)
      load()
    } catch { alert('Error deleting vendor') }
  }

  const loadBills = async (vendorId: number) => {
    try {
      const { data } = await api.get(`/vendors/${vendorId}/bills/`)
      setBills(data)
    } catch {}
  }

  const saveBill = async (e: React.FormEvent) => {
    e.preventDefault(); if (!selectedVendor) return
    setSaving(true)
    try {
      const payload = { ...bForm, amount: parseFloat(bForm.amount), tax_amount: bForm.tax_amount ? parseFloat(bForm.tax_amount) : 0 }
      if (editBill) {
        await api.patch(`/vendor-bills/${editBill.id}`, payload)
      } else {
        await api.post(`/vendors/${selectedVendor.id}/bills/`, payload)
      }
      setShowBillModal(false); setEditBill(null); setBForm({ title: '', amount: '', tax_amount: '0', tax_type: '', due_date: '' })
      loadBills(selectedVendor.id)
    } catch { alert('Error saving bill') } finally { setSaving(false) }
  }

  const handleDeleteBill = async (id: number) => {
    if (!confirm('Delete this bill?')) return
    try {
      await api.delete(`/vendor-bills/${id}`)
      if (selectedVendor) loadBills(selectedVendor.id)
    } catch { alert('Error deleting bill') }
  }

  const handlePay = async (bId: number) => {
    try {
      await api.post(`/vendor-bills/${bId}/pay`)
      if (selectedVendor) loadBills(selectedVendor.id)
    } catch { alert("Failed to mark bill as paid.") }
  }

  const openEditVendor = (v: Vendor) => {
    setEditVendor(v)
    setForm({ name: v.name, category: v.category, contact: v.contact || '' })
    setShowModal(true)
  }

  const openEditBill = (b: VendorBill) => {
    setEditBill(b)
    setBForm({ title: b.title, amount: b.amount.toString(), tax_amount: (b.tax_amount || 0).toString(), tax_type: b.tax_type || '', due_date: b.due_date.split('T')[0] })
    setShowBillModal(true)
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-20">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Vendor Management</h1>
          <p className="text-text-secondary text-sm mt-0.5">{vendors.length} vendors connected</p>
        </div>
        <button onClick={() => { setEditVendor(null); setForm({ name: '', category: 'Software', contact: '' }); setShowModal(true) }} className="btn-primary">
          <Plus size={18} /> Add Vendor
        </button>
      </div>

      {vendors.length === 0 ? (
        <div className="card py-24 flex flex-col items-center gap-4 text-text-muted">
          <Building2 size={48} className="opacity-20" />
          <p>No vendors or suppliers added yet.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {vendors.map((v, i) => (
            <motion.div
              key={v.id}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.05 }}
              className="card p-6 group relative hover:border-brand/30 transition-colors"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-brand/10 border border-brand/20 flex items-center justify-center font-bold text-brand">
                    <Store size={18} />
                  </div>
                  <div>
                    <p className="font-semibold leading-tight">{v.name}</p>
                    <p className="text-[10px] text-brand/70 uppercase tracking-wider">{v.category}</p>
                  </div>
                </div>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                   <button onClick={() => openEditVendor(v)} className="p-1.5 hover:bg-white/10 rounded-lg text-text-muted"><Edit2 size={12}/></button>
                   <button onClick={() => handleDeleteVendor(v.id)} className="p-1.5 hover:bg-white/10 rounded-lg text-red/60"><Trash2 size={12}/></button>
                </div>
              </div>

              {v.contact && (
                <div className="text-xs text-text-muted mb-4 pb-4 border-b border-white/5">
                  Contact: <span className="font-medium text-white/90">{v.contact}</span>
                </div>
              )}

              <button 
                onClick={() => { setSelectedVendor(v); loadBills(v.id) }} 
                className="btn-ghost w-full py-2.5 text-xs font-bold border-brand/20 hover:border-brand/50 mt-auto"
              >
                Manage Bills
              </button>
            </motion.div>
          ))}
        </div>
      )}

      {selectedVendor && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-40 p-4">
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col shadow-2xl">
            <div className="p-6 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
              <div className="flex items-center gap-3">
                <Store className="text-brand opacity-80" size={24} />
                <div>
                  <h2 className="text-xl font-bold">{selectedVendor.name}</h2>
                  <p className="text-[10px] text-text-muted uppercase tracking-widest font-bold">Accounts Payable (Bills)</p>
                </div>
              </div>
              <button onClick={() => setSelectedVendor(null)} className="p-2 hover:bg-white/10 rounded-xl transition-colors"><X size={20}/></button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="font-bold text-xs uppercase tracking-widest text-text-secondary">Outstanding & Past Bills</h3>
                <button onClick={() => { setEditBill(null); setBForm({ title: '', amount: '', tax_amount: '0', tax_type: '', due_date: '' }); setShowBillModal(true) }} className="btn-primary py-2 px-4 text-xs font-bold">+ Log Bill</button>
              </div>
              
              {bills.length === 0 ? (
                <p className="text-center py-12 text-text-muted text-sm italic">No bills logged for this vendor.</p>
              ) : (
                <div className="space-y-3">
                  {bills.map(b => {
                    const BIcon = statusIcon[b.status] || Clock
                    return (
                      <div key={b.id} className="card p-4 group flex items-center justify-between border-white/5 hover:bg-white/5 transition-colors">
                        <div className="space-y-1">
                          <p className="font-semibold text-sm">{b.title}</p>
                          <p className="text-[10px] text-text-muted num uppercase font-medium">Due: {new Date(b.due_date).toLocaleDateString()} · <span className="text-brand">PKR {b.amount.toLocaleString()}</span></p>
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                             <button onClick={() => openEditBill(b)} className="p-1.5 hover:bg-white/10 rounded-lg text-text-muted"><Edit2 size={12}/></button>
                             <button onClick={() => handleDeleteBill(b.id)} className="p-1.5 hover:bg-white/10 rounded-lg text-red/60"><Trash2 size={12}/></button>
                          </div>
                          <span className={`badge ${statusStyle[b.status] || 'badge-amber'}`}>
                            <BIcon size={10} /> {b.status}
                          </span>
                          {b.status !== 'Paid' && (
                            <button onClick={() => handlePay(b.id)} className="bg-brand hover:brightness-110 text-brand-darkest py-1.5 px-3 rounded-lg text-[10px] font-bold transition-all">Mark Paid</button>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </motion.div>
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="glass w-full max-w-md p-8 space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold">{editVendor ? 'Edit Vendor' : 'New Vendor'}</h2>
              <button onClick={() => setShowModal(false)}><X size={20}/></button>
            </div>
            <form onSubmit={save} className="space-y-5">
              <div className="input-group">
                <label className="input-label">Vendor Name *</label>
                <input className="input" placeholder="Supplier INC" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
              </div>
              <div className="input-group">
                <label className="input-label">Category *</label>
                <select className="input" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
                  {['Software', 'Hardware', 'Marketing', 'Office Supplies', 'Legal', 'Contractor', 'Other'].map(t => <option key={t}>{t}</option>)}
                </select>
              </div>
              <div className="input-group">
                <label className="input-label">Contact / Email</label>
                <input className="input" placeholder="contact@vendor.com" value={form.contact} onChange={(e) => setForm({ ...form, contact: e.target.value })} />
              </div>
              <button type="submit" disabled={saving} className="btn-primary w-full py-3.5 font-bold shadow-xl shadow-brand/20">
                {saving ? 'Saving…' : (editVendor ? 'Update Vendor' : 'Save Vendor')}
              </button>
            </form>
          </motion.div>
        </div>
      )}

      {showBillModal && (
        <div className="fixed inset-0 bg-black/90 flex items-center justify-center z-50 p-4">
          <motion.div initial={{ scale: 0.95 }} animate={{ scale: 1 }} className="glass w-full max-w-sm p-8 space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-bold">{editBill ? 'Edit Bill' : 'Log Bill'}</h2>
              <button onClick={() => setShowBillModal(false)}><X size={20}/></button>
            </div>
            <form onSubmit={saveBill} className="space-y-5">
              <div className="input-group">
                <label className="input-label">Bill Title / Invoice #</label>
                <input className="input" placeholder="AWS Bill March" value={bForm.title} onChange={e => setBForm({...bForm, title: e.target.value})} required />
              </div>
              <div className="input-group">
                <label className="input-label">Gross Amount (PKR)</label>
                <input className="input" type="number" placeholder="5000" value={bForm.amount} onChange={e => setBForm({...bForm, amount: e.target.value})} required />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="input-group">
                  <label className="input-label">Tax Deducted (PKR)</label>
                  <input className="input" type="number" placeholder="0" value={bForm.tax_amount} onChange={e => setBForm({...bForm, tax_amount: e.target.value})} />
                </div>
                <div className="input-group">
                  <label className="input-label">Tax Type</label>
                  <select className="input" value={bForm.tax_type} onChange={e => setBForm({...bForm, tax_type: e.target.value})}>
                    <option value="">None</option>
                    <option value="WHT">WHT</option>
                    <option value="GST">GST</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>
              <div className="input-group">
                <label className="input-label">Due Date</label>
                <input className="input" type="date" value={bForm.due_date} onChange={e => setBForm({...bForm, due_date: e.target.value})} required />
              </div>
              <button type="submit" disabled={saving} className="bg-brand text-brand-darkest hover:brightness-110 w-full py-3.5 rounded-xl font-bold transition-all shadow-xl shadow-brand/20">
                {saving ? 'Saving...' : (editBill ? 'Update Bill' : 'Log Payable')}
              </button>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  )
}
