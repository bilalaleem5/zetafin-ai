import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Mail, Lock, ArrowRight } from 'lucide-react'
import api from '../api'

export default function Login() {
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)
  const navigate = useNavigate()

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true); setError('')
    try {
      const form = new FormData()
      form.append('username', email)
      form.append('password', password)
      const { data } = await api.post('/token', form)
      localStorage.setItem('zetamize_token', data.access_token)
      navigate('/')
    } catch {
      setError('Invalid email or password. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen hero-gradient flex">
      {/* Left — Branding */}
      <div className="hidden lg:flex flex-col justify-between w-1/2 p-16 border-r border-border">
        <div className="flex items-center gap-3 w-full">
          <img src="/logo.png" alt="ZetaFin AI" className="w-full max-w-[480px] object-contain object-left drop-shadow-lg" />
        </div>

        <div className="space-y-8">
          <div className="space-y-4">
            <div className="badge badge-brand w-fit">Financial Intelligence</div>
            <h1 className="text-5xl font-black leading-tight">
              Know exactly<br />
              <span className="gradient-text">where every rupee goes.</span>
            </h1>
            <p className="text-text-secondary text-lg leading-relaxed max-w-sm">
              Real-time P&L, client tracking, and WhatsApp-powered data entry — all in one place.
            </p>
          </div>

          {/* Mini Stats */}
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: 'Live Metrics', val: '7' },
              { label: 'WhatsApp Commands', val: '5' },
              { label: 'Setup Time', val: '10m' },
            ].map((s) => (
              <div key={s.label} className="card p-4 space-y-1">
                <div className="num text-2xl font-bold text-brand">{s.val}</div>
                <div className="text-xs text-text-muted">{s.label}</div>
              </div>
            ))}
          </div>
        </div>

        <p className="text-text-muted text-sm">© 2024 ZetaFin AI — Built for Pakistani SMBs</p>
      </div>

      {/* Right — Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md space-y-8"
        >
          {/* Mobile logo */}
          <div className="flex lg:hidden items-center gap-3 mb-2">
            <img src="/logo.png" alt="ZetaFin AI" className="h-32 object-contain" />
          </div>

          <div>
            <h2 className="text-3xl font-bold">Welcome back</h2>
            <p className="text-text-secondary mt-1">Sign in to your financial dashboard</p>
          </div>

          <form onSubmit={submit} className="space-y-5">
            <div className="input-group">
              <label className="input-label">Email Address</label>
              <div className="relative">
                <Mail size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted" />
                <input
                  id="login-email"
                  type="email"
                  className="input pl-11"
                  placeholder="owner@business.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="input-group">
              <label className="input-label">Password</label>
              <div className="relative">
                <Lock size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted" />
                <input
                  id="login-password"
                  type="password"
                  className="input pl-11"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
            </div>

            {error && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="badge badge-red w-full justify-start py-3 text-sm rounded-xl px-4"
              >
                {error}
              </motion.div>
            )}

            <button
              id="login-submit"
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-3.5 text-base group"
            >
              {loading ? 'Signing in…' : (
                <>Sign In <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" /></>
              )}
            </button>
          </form>

          <p className="text-center text-text-secondary text-sm">
            No account?{' '}
            <Link to="/register" className="text-brand font-semibold hover:underline">
              Create one free →
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  )
}
