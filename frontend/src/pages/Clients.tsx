import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Plus, Users, CheckCircle2, Clock, AlertTriangle, X, Edit2, Trash2, FileText } from 'lucide-react'
import api from '../api'
import { useReactToPrint } from 'react-to-print'
import { InvoiceDocument, InvoiceUser } from '../components/InvoiceDocument'

interface Milestone { id: number; title: string; amount: number; due_date: string; status: string; tax_amount: number; tax_type: string; }
interface Client { id: number; name: string; contract_value: number; payment_terms: string; status: string }

const statusStyle: Record<string, string> = {
  Paid:    'badge-green',
  Pending: 'badge-amber',
  Overdue: 'badge-red',
  Partial: 'badge-brand',
  Disputed: 'badge-red opacity-70',
  Advance: 'badge-teal',
}
const statusIcon: Record<string, any> = {
  Paid: CheckCircle2, Pending: Clock, Overdue: AlertTriangle,
  Partial: Clock, Disputed: AlertTriangle, Advance: CheckCircle2,
}

export default function Clients() {
  const [clients, setClients] = useState<Client[]>([])
  const [showModal, setShowModal] = useState(false)
  const [showMilestoneModal, setShowMilestoneModal] = useState(false)
  const [selectedClient, setSelectedClient] = useState<Client | null>(null)
  const [editClient, setEditClient] = useState<Client | null>(null)
  const [editMilestone, setEditMilestone] = useState<Milestone | null>(null)
  
  const [milestones, setMilestones] = useState<Milestone[]>([])
  const [form, setForm] = useState({ name: '', contract_value: '', payment_terms: 'Net 30' })
  const [mForm, setMForm] = useState({ title: '', amount: '', tax_amount: '0', tax_type: '', due_date: '' })
  const [saving, setSaving] = useState(false)
  const [user, setUser] = useState<InvoiceUser | null>(null)
  const [printingMilestone, setPrintingMilestone] = useState<Milestone | null>(null)
  
  const invoiceRef = React.useRef<HTMLDivElement>(null)
  const handlePrint = useReactToPrint({
    contentRef: invoiceRef,
    documentTitle: 'Invoice',
    onAfterPrint: () => setPrintingMilestone(null)
  });

  const printInvoice = (m: Milestone) => {
    setPrintingMilestone(m);
    setTimeout(handlePrint, 100);
  };

  const load = async () => {
    try { 
      const { data } = await api.get('/clients/'); setClients(data) 
      const res = await api.get('/users/me'); setUser(res.data)
    } catch {}
  }
  useEffect(() => { load() }, [])

  const save = async (e: React.FormEvent) => {
    e.preventDefault(); setSaving(true)
    try {
      if (editClient) {
        await api.patch(`/clients/${editClient.id}`, { ...form, contract_value: parseFloat(form.contract_value) })
      } else {
        await api.post('/clients/', { ...form, contract_value: parseFloat(form.contract_value) })
      }
      setShowModal(false); setEditClient(null); setForm({ name: '', contract_value: '', payment_terms: 'Net 30' })
      load()
    } catch { alert('Error saving client') } finally { setSaving(false) }
  }

  const handleDeleteClient = async (id: number) => {
    if (!confirm('Are you sure? This will delete the client and all associated milestones.')) return
    try {
      await api.delete(`/clients/${id}`)
      load()
    } catch { alert('Error deleting client') }
  }

  const loadMilestones = async (clientId: number) => {
    try {
      const { data } = await api.get(`/clients/${clientId}/milestones/`)
      setMilestones(data)
    } catch {}
  }

  const saveMilestone = async (e: React.FormEvent) => {
    e.preventDefault(); if (!selectedClient) return
    setSaving(true)
    try {
      const payload = { ...mForm, amount: parseFloat(mForm.amount), tax_amount: mForm.tax_amount ? parseFloat(mForm.tax_amount) : 0 }
      if (editMilestone) {
        await api.patch(`/milestones/${editMilestone.id}`, payload)
      } else {
        await api.post(`/clients/${selectedClient.id}/milestones/`, payload)
      }
      setShowMilestoneModal(false); setEditMilestone(null); setMForm({ title: '', amount: '', tax_amount: '0', tax_type: '', due_date: '' })
      loadMilestones(selectedClient.id)
    } catch { alert('Error saving milestone') } finally { setSaving(false) }
  }

  const handleDeleteMilestone = async (id: number) => {
    if (!confirm('Delete this milestone?')) return
    try {
      await api.delete(`/milestones/${id}`)
      if (selectedClient) loadMilestones(selectedClient.id)
    } catch { alert('Error deleting milestone') }
  }

  const handleReceive = async (mId: number) => {
    try {
      await api.post(`/milestones/${mId}/receive`)
      if (selectedClient) loadMilestones(selectedClient.id)
    } catch { alert("Failed to receive payment.") }
  }

  const openEditClient = (c: Client) => {
    setEditClient(c)
    setForm({ name: c.name, contract_value: c.contract_value.toString(), payment_terms: c.payment_terms })
    setShowModal(true)
  }

  const openEditMilestone = (m: Milestone) => {
    setEditMilestone(m)
    setMForm({ title: m.title, amount: m.amount.toString(), tax_amount: (m.tax_amount || 0).toString(), tax_type: m.tax_type || '', due_date: m.due_date.split('T')[0] })
    setShowMilestoneModal(true)
  }

  const totalOutstanding = clients
    .filter(c => c.status !== 'Paid')
    .reduce((a, c) => a + c.contract_value, 0)

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-20">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Client Management</h1>
          <p className="text-text-secondary text-sm mt-0.5">{clients.length} active clients · PKR {totalOutstanding.toLocaleString()} outstanding</p>
        </div>
        <button onClick={() => { setEditClient(null); setForm({ name: '', contract_value: '', payment_terms: 'Net 30' }); setShowModal(true) }} className="btn-primary">
          <Plus size={18} /> Add Client
        </button>
      </div>

      {clients.length === 0 ? (
        <div className="card py-24 flex flex-col items-center gap-4 text-text-muted">
          <Users size={48} className="opacity-20" />
          <p>No clients yet.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {clients.map((c, i) => {
            const Icon = statusIcon[c.status] ?? Clock
            return (
              <motion.div
                key={c.id}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="card p-6 group relative hover:border-brand/30 transition-colors"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-11 h-11 rounded-xl bg-brand/10 border border-brand/20 flex items-center justify-center font-bold text-brand">
                      {c.name[0].toUpperCase()}
                    </div>
                    <div>
                      <p className="font-semibold">{c.name}</p>
                      <p className="text-[10px] text-text-muted uppercase">{c.payment_terms}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity mr-2">
                       <button onClick={() => openEditClient(c)} className="p-1.5 hover:bg-white/10 rounded-lg text-text-muted"><Edit2 size={12}/></button>
                       <button onClick={() => handleDeleteClient(c.id)} className="p-1.5 hover:bg-white/10 rounded-lg text-red/60"><Trash2 size={12}/></button>
                    </div>
                    <span className={`badge ${statusStyle[c.status] ?? 'badge-muted'}`}>
                      <Icon size={10} /> {c.status}
                    </span>
                  </div>
                </div>
                <div className="flex justify-between items-center mb-4 bg-white/5 p-3 rounded-xl">
                  <span className="text-text-muted text-xs uppercase tracking-wider font-medium">Contract Value</span>
                  <span className="num font-bold text-lg">PKR {c.contract_value.toLocaleString()}</span>
                </div>
                <button 
                  onClick={() => { setSelectedClient(c); loadMilestones(c.id) }} 
                  className="btn-ghost w-full py-2.5 text-xs font-bold text-brand border-brand/20 hover:border-brand/50"
                >
                  Manage Milestones
                </button>
              </motion.div>
            )
          })}
        </div>
      )}

      {selectedClient && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-40 p-4">
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col shadow-2xl">
            <div className="p-6 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
              <div>
                <h2 className="text-xl font-bold">{selectedClient.name}</h2>
                <p className="text-[10px] text-text-muted uppercase tracking-widest font-bold">Payment Milestones</p>
              </div>
              <button onClick={() => setSelectedClient(null)} className="p-2 hover:bg-white/10 rounded-xl transition-colors"><X size={20}/></button>
            </div>
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="font-bold text-xs uppercase tracking-widest text-text-secondary">All Milestones</h3>
                <button onClick={() => { setEditMilestone(null); setMForm({ title: '', amount: '', tax_amount: '0', tax_type: '', due_date: '' }); setShowMilestoneModal(true) }} className="btn-primary py-2 px-4 text-xs font-bold">+ Add New</button>
              </div>
              {milestones.length === 0 ? (
                <p className="text-center py-12 text-text-muted text-sm italic">No milestones defined.</p>
              ) : (
                <div className="space-y-3">
                  {milestones.map(m => (
                    <div key={m.id} className="card p-4 group flex items-center justify-between border-white/5 hover:bg-white/5 transition-colors">
                      <div className="space-y-1">
                        <p className="font-semibold text-sm">{m.title}</p>
                        <p className="text-[10px] text-text-muted num uppercase font-medium">Due: {new Date(m.due_date).toLocaleDateString()} · <span className="text-brand">PKR {m.amount.toLocaleString()}</span></p>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                           <button onClick={() => openEditMilestone(m)} className="p-1.5 hover:bg-white/10 rounded-lg text-text-muted"><Edit2 size={12}/></button>
                           <button onClick={() => handleDeleteMilestone(m.id)} className="p-1.5 hover:bg-white/10 rounded-lg text-red/60"><Trash2 size={12}/></button>
                        </div>
                        <span className={`badge ${statusStyle[m.status] || 'badge-amber'}`}>
                          {m.status}
                        </span>
                        {m.status !== 'Paid' && (
                          <div className="flex gap-2">
                             <button onClick={() => printInvoice(m)} className="btn-ghost py-1.5 px-3 text-[10px] font-bold flex items-center gap-1.5"><FileText size={12}/> Invoice</button>
                             <button onClick={() => handleReceive(m.id)} className="btn-primary py-1.5 px-3 text-[10px] font-bold">Mark Received</button>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        </div>
      )}

      {showMilestoneModal && (
        <div className="fixed inset-0 bg-black/90 flex items-center justify-center z-50 p-4">
          <motion.div initial={{ scale: 0.95 }} animate={{ scale: 1 }} className="glass w-full max-w-sm p-8 space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-bold">{editMilestone ? 'Edit Milestone' : 'Add Milestone'}</h2>
              <button onClick={() => setShowMilestoneModal(false)}><X size={20}/></button>
            </div>
            <form onSubmit={saveMilestone} className="space-y-5">
              <div className="input-group">
                <label className="input-label">Title</label>
                <input className="input" placeholder="Initial Advance" value={mForm.title} onChange={e => setMForm({...mForm, title: e.target.value})} required />
              </div>
              <div className="input-group">
                <label className="input-label">Gross Amount (PKR)</label>
                <input className="input" type="number" placeholder="50000" value={mForm.amount} onChange={e => setMForm({...mForm, amount: e.target.value})} required />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="input-group">
                  <label className="input-label">Tax Withheld (PKR)</label>
                  <input className="input" type="number" placeholder="0" value={mForm.tax_amount} onChange={e => setMForm({...mForm, tax_amount: e.target.value})} />
                </div>
                <div className="input-group">
                  <label className="input-label">Tax Type</label>
                  <select className="input" value={mForm.tax_type} onChange={e => setMForm({...mForm, tax_type: e.target.value})}>
                    <option value="">None</option>
                    <option value="WHT">WHT</option>
                    <option value="GST">GST</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>
              <div className="input-group">
                <label className="input-label">Due Date</label>
                <input className="input" type="date" value={mForm.due_date} onChange={e => setMForm({...mForm, due_date: e.target.value})} required />
              </div>
              <button type="submit" disabled={saving} className="btn-primary w-full py-3.5 font-bold shadow-xl shadow-brand/20">
                {saving ? 'Saving...' : (editMilestone ? 'Update Milestone' : 'Create Milestone')}
              </button>
            </form>
          </motion.div>
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="glass w-full max-w-md p-8 space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold">{editClient ? 'Edit Client' : 'New Client'}</h2>
              <button onClick={() => setShowModal(false)}><X size={20}/></button>
            </div>
            <form onSubmit={save} className="space-y-5">
              <div className="input-group">
                <label className="input-label">Client Name</label>
                <input className="input" placeholder="Ali Traders" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
              </div>
              <div className="input-group">
                <label className="input-label">Contract Value (PKR)</label>
                <input className="input" type="number" placeholder="500000" value={form.contract_value} onChange={(e) => setForm({ ...form, contract_value: e.target.value })} required />
              </div>
              <div className="input-group">
                <label className="input-label">Payment Terms</label>
                <select className="input" value={form.payment_terms} onChange={(e) => setForm({ ...form, payment_terms: e.target.value })}>
                  {['Net 15', 'Net 30', 'Net 45', 'Net 60', 'Advance'].map(t => <option key={t}>{t}</option>)}
                </select>
              </div>
              <button type="submit" disabled={saving} className="btn-primary w-full py-3.5 font-bold shadow-xl shadow-brand/20">
                {saving ? 'Saving…' : (editClient ? 'Update Client' : 'Save Client')}
              </button>
            </form>
          </motion.div>
        </div>
      )}

      <div className="hidden">
        {(printingMilestone && selectedClient && user) ? (
          <InvoiceDocument
            ref={invoiceRef}
            user={user}
            client={selectedClient}
            milestone={printingMilestone}
          />
        ) : null}
      </div>
    </div>
  )
}
