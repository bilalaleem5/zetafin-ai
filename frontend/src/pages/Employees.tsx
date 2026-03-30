import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Plus, UserCheck, X, Edit2, Trash2 } from 'lucide-react'
import api from '../api'

interface Employee { id: number; name: string; role: string; salary: number; join_date: string }

export default function Employees() {
  const [emps, setEmps]       = useState<Employee[]>([])
  const [paidIds, setPaidIds] = useState<number[]>([])
  const [showModal, setModal] = useState(false)
  const [editEmp, setEditEmp] = useState<Employee | null>(null)
  const [form, setForm]       = useState({ name: '', role: '', salary: '' })
  const [saving, setSaving]   = useState(false)
  const [paying, setPaying]   = useState<number | null>(null)

  const load = async () => {
    try { 
      const [empRes, statRes] = await Promise.all([
        api.get('/employees/'),
        api.get('/dashboard-stats')
      ])
      setEmps(empRes.data)
      setPaidIds(statRes.data.paid_employee_ids || [])
    } catch {}
  }
  useEffect(() => { load() }, [])

  const save = async (e: React.FormEvent) => {
    e.preventDefault(); setSaving(true)
    try {
      if (editEmp) {
        await api.patch(`/employees/${editEmp.id}`, { ...form, salary: parseFloat(form.salary) })
      } else {
        await api.post('/employees/', { ...form, salary: parseFloat(form.salary) })
      }
      setModal(false); setEditEmp(null); setForm({ name: '', role: '', salary: '' }); load()
    } catch { alert('Error saving employee') } finally { setSaving(false) }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to remove this team member?')) return
    try {
      await api.delete(`/employees/${id}`)
      load()
    } catch { alert('Error deleting employee') }
  }

  const openEdit = (emp: Employee) => {
    setEditEmp(emp)
    setForm({ name: emp.name, role: emp.role, salary: emp.salary.toString() })
    setModal(true)
  }

  const handlePay = async (id: number) => {
    setPaying(id)
    try {
      await api.post(`/employees/${id}/pay`)
      alert('Salary payment logged successfully!')
      load()
    } catch (err) {
      console.error(err)
      alert('Failed to process salary payment.')
    } finally {
      setPaying(null)
    }
  }

  const totalPayroll = emps.reduce((a, e) => a + e.salary, 0)

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-20">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Team Management</h1>
          <p className="text-text-secondary text-sm mt-0.5">
            {emps.length} members · Monthly payroll: <span className="num text-text-primary font-semibold">PKR {totalPayroll.toLocaleString()}</span>
          </p>
        </div>
        <button onClick={() => { setEditEmp(null); setForm({ name: '', role: '', salary: '' }); setModal(true) }} className="btn-primary">
          <Plus size={18} /> Add Member
        </button>
      </div>

      {emps.length === 0 ? (
        <div className="card py-24 flex flex-col items-center gap-4 text-text-muted">
          <Plus size={48} className="opacity-20" />
          <p>No team members yet.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {emps.map((emp, i) => (
            <motion.div
              key={emp.id}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="card p-6 space-y-4 group relative hover:border-brand/30 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand to-purple-500 flex items-center justify-center font-bold text-white text-sm">
                    {emp.name[0].toUpperCase()}
                  </div>
                  <div>
                    <p className="font-semibold">{emp.name}</p>
                    <p className="text-[10px] text-text-muted uppercase">{emp.role}</p>
                  </div>
                </div>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button onClick={() => openEdit(emp)} className="p-1.5 hover:bg-white/10 rounded-lg text-text-muted"><Edit2 size={12}/></button>
                  <button onClick={() => handleDelete(emp.id)} className="p-1.5 hover:bg-white/10 rounded-lg text-red/60"><Trash2 size={12}/></button>
                </div>
              </div>
              
              <div className="divider my-0 opacity-10" />
              
              <div className="flex justify-between items-center bg-white/5 p-3 rounded-xl">
                <span className="text-text-muted text-xs">Monthly Salary</span>
                <span className="num font-bold text-brand">PKR {emp.salary.toLocaleString()}</span>
              </div>

              {paidIds.includes(emp.id) ? (
                <div className="flex items-center justify-center gap-2 py-2.5 bg-green/5 text-green rounded-xl text-xs font-semibold border border-green/10">
                  <UserCheck size={14} /> Paid for {new Date().toLocaleString('default', { month: 'long' })}
                </div>
              ) : (
                <button 
                  onClick={() => handlePay(emp.id)}
                  disabled={paying === emp.id}
                  className={`btn-primary-outline w-full py-2.5 text-xs font-bold ${paying === emp.id ? 'opacity-50' : ''}`}
                >
                  {paying === emp.id ? 'Processing...' : 'Mark Paid'}
                </button>
              )}
            </motion.div>
          ))}
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="glass w-full max-w-md p-8 space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold">{editEmp ? 'Edit Member' : 'Add Team Member'}</h2>
              <button onClick={() => setModal(false)}><X size={20}/></button>
            </div>
            <form onSubmit={save} className="space-y-4">
              <div className="input-group">
                <label className="input-label">Full Name</label>
                <input className="input" placeholder="Ahmad Raza" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
              </div>
              <div className="input-group">
                <label className="input-label">Role / Position</label>
                <input className="input" placeholder="Sales Manager" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} required />
              </div>
              <div className="input-group">
                <label className="input-label">Monthly Salary (PKR)</label>
                <input className="input" type="number" placeholder="85000" value={form.salary} onChange={(e) => setForm({ ...form, salary: e.target.value })} required />
              </div>
              <button type="submit" disabled={saving} className="btn-primary w-full py-3.5 mt-2 shadow-xl shadow-brand/20">
                {saving ? 'Saving…' : (editEmp ? 'Update Member' : 'Add Member')}
              </button>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  )
}
