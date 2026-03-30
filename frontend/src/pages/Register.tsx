import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Mail, Lock, Building2, Phone, Briefcase, ArrowRight, Check } from 'lucide-react'
import api from '../api'

const industries = ['Retail', 'Services', 'SaaS / Tech', 'Manufacturing', 'E-Commerce', 'Consulting', 'Other']

export default function Register() {
  const [form, setForm] = useState({
    email: '', password: '', business_name: '',
    industry: 'Retail', whatsapp_number: '', currency: 'PKR',
  })
  const [error, setError]     = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm({ ...form, [k]: e.target.value })

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true); setError('')
    try {
      await api.post('/register', form)
      // auto-login
      const fd = new FormData()
      fd.append('username', form.email); fd.append('password', form.password)
      const { data } = await api.post('/token', fd)
      localStorage.setItem('zetamize_token', data.access_token)
      navigate('/onboarding')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen hero-gradient flex items-center justify-center p-6">
      <motion.div
        initial={{ opacity: 0, y: 28 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55 }}
        className="w-full max-w-2xl"
      >
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-3 mb-6">
            <img src="/logo.png" alt="ZetaFin AI" className="h-48 object-contain" />
          </div>
          <h1 className="text-4xl font-black">Start for free</h1>
          <p className="text-text-secondary mt-2">Get full financial clarity in under 10 minutes.</p>
        </div>

        <div className="card p-8 space-y-6">
          {/* Perks row */}
          <div className="grid grid-cols-3 gap-3 pb-6 border-b border-border">
            {['Zero setup cost', 'WhatsApp included', 'No accounting degree'].map((p) => (
              <div key={p} className="flex items-center gap-2 text-sm text-text-secondary">
                <div className="w-5 h-5 rounded-full bg-green/10 flex items-center justify-center flex-shrink-0">
                  <Check size={10} className="text-green" />
                </div>
                {p}
              </div>
            ))}
          </div>

          <form onSubmit={submit} className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="input-group md:col-span-2">
              <label className="input-label">Business Email</label>
              <div className="relative">
                <Mail size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted" />
                <input id="reg-email" type="email" className="input pl-11" placeholder="owner@business.com" value={form.email} onChange={set('email')} required />
              </div>
            </div>

            <div className="input-group">
              <label className="input-label">Business Name</label>
              <div className="relative">
                <Building2 size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted" />
                <input id="reg-biz" type="text" className="input pl-11" placeholder="Acme Trading Co." value={form.business_name} onChange={set('business_name')} required />
              </div>
            </div>

            <div className="input-group">
              <label className="input-label">Industry</label>
              <div className="relative">
                <Briefcase size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted" />
                <select id="reg-industry" className="input pl-11 appearance-none cursor-pointer" value={form.industry} onChange={set('industry')}>
                  {industries.map((i) => <option key={i}>{i}</option>)}
                </select>
              </div>
            </div>

            <div className="input-group">
              <label className="input-label">WhatsApp Number</label>
              <div className="relative">
                <Phone size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted" />
                <input id="reg-wa" type="tel" className="input pl-11" placeholder="+92 300 1234567" value={form.whatsapp_number} onChange={set('whatsapp_number')} required />
              </div>
            </div>

            <div className="input-group">
              <label className="input-label">Base Currency</label>
              <select id="reg-currency" className="input cursor-pointer" value={form.currency} onChange={set('currency')}>
                <option value="PKR">PKR — Pakistani Rupee</option>
                <option value="USD">USD — US Dollar</option>
              </select>
            </div>

            <div className="input-group md:col-span-2">
              <label className="input-label">Password</label>
              <div className="relative">
                <Lock size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted" />
                <input id="reg-pass" type="password" className="input pl-11" placeholder="Min. 8 characters" value={form.password} onChange={set('password')} required minLength={8} />
              </div>
            </div>

            {error && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="md:col-span-2 badge badge-red w-full justify-start py-3 text-sm rounded-xl px-4">
                {error}
              </motion.div>
            )}

            <button id="reg-submit" type="submit" disabled={loading} className="btn-primary md:col-span-2 py-3.5 text-base group">
              {loading ? 'Creating account…' : <>Create Free Account <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" /></>}
            </button>
          </form>
        </div>

        <p className="text-center text-text-muted text-sm mt-6">
          Already have an account?{' '}
          <Link to="/login" className="text-brand font-semibold hover:underline">Sign in →</Link>
        </p>
      </motion.div>
    </div>
  )
}
