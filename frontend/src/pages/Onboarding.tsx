import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Users, Briefcase, MessageSquare, Check, ArrowRight, ArrowLeft, Plus } from 'lucide-react'
import api from '../api'

const STEPS = [
  { id: 1, title: 'Build Your Team',     sub: 'Add employees and monthly salaries.',             icon: Users },
  { id: 2, title: 'Add Your Clients',    sub: 'Add active clients and contract values.',         icon: Briefcase },
  { id: 3, title: 'Activate WhatsApp',   sub: 'Your bot is ready. Try a command below.',        icon: MessageSquare },
]

export default function Onboarding() {
  const [step, setStep] = useState(1)
  const [employees, setEmployees] = useState<any[]>([])
  const [clients, setClients]     = useState<any[]>([])
  const [empForm, setEmpForm]     = useState({ name: '', role: '', salary: '' })
  const [cliForm, setCliForm]     = useState({ name: '', contract_value: '', payment_terms: 'Net 30' })
  const navigate = useNavigate()

  const addEmployee = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const { data } = await api.post('/employees/', { ...empForm, salary: parseFloat(empForm.salary) })
      setEmployees([...employees, data])
      setEmpForm({ name: '', role: '', salary: '' })
      alert('Employee added to your team!')
    } catch (err) {
      alert('Failed to add employee. Please check inputs.')
    }
  }

  const addClient = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const { data } = await api.post('/clients/', { ...cliForm, contract_value: parseFloat(cliForm.contract_value) })
      setClients([...clients, data])
      setCliForm({ name: '', contract_value: '', payment_terms: 'Net 30' })
      alert('Client added successfully!')
    } catch (err) {
      alert('Failed to add client. Check the contract value.')
    }
  }

  const S = STEPS[step - 1]

  return (
    <div className="min-h-screen hero-gradient flex flex-col items-center justify-center p-6">
      {/* Logo */}
      <div className="flex items-center gap-3 mb-10">
        <img src="/logo.png" alt="ZetaFin AI Setup" className="h-32 object-contain" />
      </div>

      {/* Step indicator */}
      <div className="flex items-center gap-3 mb-8">
        {STEPS.map((s, i) => (
          <React.Fragment key={s.id}>
            <div className={`flex items-center justify-center w-9 h-9 rounded-full font-bold text-sm transition-all duration-400 ${
              step > s.id ? 'bg-green text-white' : step === s.id ? 'bg-brand text-white shadow-lg glow-brand' : 'bg-bg-card border border-border text-text-muted'
            }`}>
              {step > s.id ? <Check size={16} /> : s.id}
            </div>
            {i < STEPS.length - 1 && (
              <div className={`h-px w-16 transition-colors duration-400 ${step > s.id ? 'bg-green' : 'bg-border'}`} />
            )}
          </React.Fragment>
        ))}
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={step}
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -30 }}
          transition={{ duration: 0.3 }}
          className="w-full max-w-xl"
        >
          <div className="card p-8 space-y-7">
            {/* Step header */}
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-2xl bg-brand/10 border border-brand/20">
                <S.icon size={22} className="text-brand" />
              </div>
              <div>
                <h2 className="text-2xl font-bold">{S.title}</h2>
                <p className="text-text-secondary text-sm">{S.sub}</p>
              </div>
            </div>

            {/* Step 1 — Employees */}
            {step === 1 && (
              <div className="space-y-5">
                <form onSubmit={addEmployee} className="grid grid-cols-3 gap-3">
                  <input className="input col-span-3 sm:col-span-1" placeholder="Name" value={empForm.name} onChange={(e) => setEmpForm({ ...empForm, name: e.target.value })} required />
                  <input className="input" placeholder="Role" value={empForm.role} onChange={(e) => setEmpForm({ ...empForm, role: e.target.value })} required />
                  <div className="flex gap-2">
                    <input className="input flex-1" type="number" placeholder="Salary" value={empForm.salary} onChange={(e) => setEmpForm({ ...empForm, salary: e.target.value })} required />
                    <button type="submit" className="btn-ghost px-3"><Plus size={18} /></button>
                  </div>
                </form>
                {employees.length > 0 && (
                  <div className="space-y-2">
                    {employees.map((e, i) => (
                      <div key={i} className="card-elevated flex justify-between items-center px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-brand/20 flex items-center justify-center text-sm font-bold text-brand">{e.name[0]}</div>
                          <div>
                            <p className="text-sm font-medium">{e.name}</p>
                            <p className="text-xs text-text-muted">{e.role}</p>
                          </div>
                        </div>
                        <span className="num text-sm font-semibold">PKR {Number(e.salary).toLocaleString()}</span>
                      </div>
                    ))}
                    <div className="flex justify-between text-sm px-1">
                      <span className="text-text-muted">Total monthly payroll</span>
                      <span className="num font-bold text-brand">PKR {employees.reduce((a, e) => a + Number(e.salary), 0).toLocaleString()}</span>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Step 2 — Clients */}
            {step === 2 && (
              <div className="space-y-5">
                <form onSubmit={addClient} className="grid grid-cols-3 gap-3">
                  <input className="input col-span-3 sm:col-span-1" placeholder="Client Name" value={cliForm.name} onChange={(e) => setCliForm({ ...cliForm, name: e.target.value })} required />
                  <input className="input" type="number" placeholder="Contract Value" value={cliForm.contract_value} onChange={(e) => setCliForm({ ...cliForm, contract_value: e.target.value })} required />
                  <div className="flex gap-2">
                    <select className="input flex-1" value={cliForm.payment_terms} onChange={(e) => setCliForm({ ...cliForm, payment_terms: e.target.value })}>
                      {['Net 15','Net 30','Net 45','Advance'].map(t => <option key={t}>{t}</option>)}
                    </select>
                    <button type="submit" className="btn-ghost px-3"><Plus size={18} /></button>
                  </div>
                </form>
                {clients.length > 0 && (
                  <div className="space-y-2">
                    {clients.map((c, i) => (
                      <div key={i} className="card-elevated flex justify-between items-center px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-green/10 flex items-center justify-center text-sm font-bold text-green">{c.name[0]}</div>
                          <div>
                            <p className="text-sm font-medium">{c.name}</p>
                            <p className="text-xs text-text-muted">{c.payment_terms}</p>
                          </div>
                        </div>
                        <span className="num text-sm font-semibold text-green">PKR {Number(c.contract_value).toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Step 3 — WhatsApp */}
            {step === 3 && (
              <div className="space-y-5">
                <div className="card-elevated p-5 space-y-4">
                  <p className="text-sm font-semibold text-text-secondary uppercase tracking-wider">Command Examples</p>
                  {[
                    { cmd: 'in 150000 Ali-Traders March-invoice', desc: 'Log income from Ali Traders' },
                    { cmd: 'ex 8500 marketing Facebook-ads',      desc: 'Log a marketing expense' },
                    { cmd: 'salary Ahmad',                         desc: 'Mark Ahmad\'s salary as paid' },
                    { cmd: 'summary',                              desc: 'Get this month\'s summary' },
                  ].map((c) => (
                    <div key={c.cmd} className="space-y-0.5">
                      <code className="text-sm font-mono text-brand bg-brand/5 px-3 py-1.5 rounded-lg block">{c.cmd}</code>
                      <p className="text-xs text-text-muted pl-1">{c.desc}</p>
                    </div>
                  ))}
                </div>
                <div className="badge badge-green w-full justify-center py-3 text-sm rounded-xl">
                  <Check size={14} /> Bot activated — save +92-xxx-xxxxxxx in WhatsApp
                </div>
              </div>
            )}

            {/* Navigation */}
            <div className="flex justify-between items-center pt-2 border-t border-border">
              <button
                onClick={() => step > 1 ? setStep(step - 1) : null}
                className={`btn-ghost text-sm py-2 ${step === 1 ? 'invisible' : ''}`}
              >
                <ArrowLeft size={16} /> Back
              </button>
              <button
                onClick={() => step === 3 ? navigate('/') : setStep(step + 1)}
                className="btn-primary text-sm py-2.5 group"
              >
                {step === 3 ? 'Go to Dashboard' : 'Continue'}
                <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
              </button>
            </div>
          </div>

          <p className="text-center text-text-muted text-xs mt-4">You can add more data anytime from the dashboard.</p>
        </motion.div>
      </AnimatePresence>
    </div>
  )
}
