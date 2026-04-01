import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  TrendingUp, TrendingDown, Clock, Wallet, Calendar,
  AlertTriangle, RefreshCw
} from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer
} from 'recharts'
import api from '../api'
import AIConsultant from '../components/AIConsultant'

// ── Shimmer placeholder ──────────────────────────────────────────────────────
const Shimmer = ({ className = '' }: { className?: string }) => (
  <div className={`shimmer rounded-xl ${className}`} />
)

// ── Individual stat card ─────────────────────────────────────────────────────
const StatCard = ({
  label, value, sub, icon: Icon, accent, loading, delay = 0
}: {
  label: string; value: string; sub?: string
  icon: React.ElementType; accent: string; loading: boolean; delay?: number
}) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.4, delay }}
    className={`card p-6 ${accent} pl-7 hover:shadow-lg transition-shadow`}
  >
    {loading ? (
      <div className="space-y-3">
        <Shimmer className="h-4 w-24" />
        <Shimmer className="h-8 w-32" />
        <Shimmer className="h-3 w-16" />
      </div>
    ) : (
      <>
        <div className="flex justify-between items-start mb-4">
          <span className="text-text-secondary text-sm font-medium">{label}</span>
          <div className="p-2 rounded-lg bg-white/5">
            <Icon size={16} className="text-text-muted" />
          </div>
        </div>
        <div className="num text-3xl font-bold">{value}</div>
        {sub && <div className="text-text-muted text-xs mt-1">{sub}</div>}
      </>
    )}
  </motion.div>
)

// ── Custom Recharts tooltip ───────────────────────────────────────────────────
const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="glass px-4 py-3 text-sm space-y-1">
      <p className="text-text-secondary font-medium mb-2">{label}</p>
      {payload.map((p: any) => (
        <div key={p.name} className="flex justify-between gap-6">
          <span style={{ color: p.color }}>{p.name}</span>
          <span className="num font-semibold">{Number(p.value).toLocaleString()}</span>
        </div>
      ))}
    </div>
  )
}

// ── Sample 6-month trend (used if no real data) ───────────────────────────────
const SAMPLE_TREND = [
  { month: 'Oct', Income: 280000, Expenses: 195000, Net: 85000 },
  { month: 'Nov', Income: 310000, Expenses: 210000, Net: 100000 },
  { month: 'Dec', Income: 360000, Expenses: 240000, Net: 120000 },
  { month: 'Jan', Income: 295000, Expenses: 185000, Net: 110000 },
  { month: 'Feb', Income: 340000, Expenses: 220000, Net: 120000 },
  { month: 'Mar', Income: 420000, Expenses: 255000, Net: 165000 },
]

// ────────────────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const [stats, setStats]       = useState<any>(null)
  const [loading, setLoading]   = useState(true)
  const [balanceInput, setBalanceInput] = useState('')
  const [period, setPeriod]     = useState('this_month')
  
  const currency                = stats?.currency ?? 'PKR'
  const fmt = (n: number) => `${currency} ${n.toLocaleString()}`

  const load = async () => {
    setLoading(true)
    try {
      const { data } = await api.get(`/dashboard-stats?period=${period}`)
      setStats(data)
      setBalanceInput(data.bank_balance.toString())
    } catch { /* empty */ }
    finally { setLoading(false) }
  }

  const saveBalance = async () => {
    if (!balanceInput) return
    try {
      await api.patch('/users/me/balance', { balance: parseFloat(balanceInput) })
      alert('Bank balance updated!')
      load()
    } catch { alert('Error updating balance') }
  }

  useEffect(() => { load() }, [period])

  const net      = stats?.net_position ?? 0
  const netPos   = net >= 0
  const periodLabel = period === 'all_time' ? 'All Time' : period === 'this_year' ? 'This Year' : period === 'last_month' ? 'Last Month' : 'This Month'

  const statCards = [
    { label: `Income (${periodLabel})`, value: fmt(stats?.total_income ?? 0),
      sub: 'Total earnings', icon: TrendingUp, accent: 'accent-left-green', delay: 0.05 },
    { label: `Expenses (${periodLabel})`, value: fmt(stats?.total_expense ?? 0),
      sub: 'Total spending', icon: TrendingDown, accent: 'accent-left-red', delay: 0.1 },
    { label: 'Cash Runway', value: `${stats?.runway_weeks ?? 0} Weeks`,
      sub: `Based on 30-day burn`, icon: Clock, accent: 'accent-left-amber', delay: 0.15 },
    { label: 'Bank Balance', value: fmt(stats?.bank_balance ?? 0),
      sub: 'Liquid Capital', icon: Wallet, accent: 'accent-left-brand', delay: 0.2 },
  ]

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Financial Intelligence</h1>
          <p className="text-text-secondary text-sm mt-0.5">{stats?.period_name || 'Loading period...'} · Real-time Analysis</p>
        </div>
        <div className="flex items-center gap-3">
          <select 
            value={period} 
            onChange={(e) => setPeriod(e.target.value)}
            className="input-field py-2 px-3 text-sm w-40 bg-white/5 border-white/10"
          >
            <option value="this_month">This Month</option>
            <option value="last_month">Last Month</option>
            <option value="this_year">This Year</option>
            <option value="all_time">All Time</option>
          </select>
          <button onClick={load} className="btn-ghost flex items-center gap-2 text-sm py-2 px-3">
            <RefreshCw size={15} /> Refresh
          </button>
        </div>
      </div>

      {/* ── Hero: Net Position ─────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, scale: 0.97 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="relative overflow-hidden rounded-3xl p-8 md:p-12"
        style={{
          background: netPos
            ? 'linear-gradient(135deg, #065f46 0%, #0f2d24 60%, #060608 100%)'
            : 'linear-gradient(135deg, #7f1d1d 0%, #2d1313 60%, #060608 100%)',
        }}
      >
        {/* Background glow */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            backgroundImage: netPos
              ? 'radial-gradient(ellipse at 80% 50%, rgba(16,185,129,0.18) 0%, transparent 70%)'
              : 'radial-gradient(ellipse at 80% 50%, rgba(244,63,94,0.18) 0%, transparent 70%)',
          }}
        />

        <div className="relative z-10 flex flex-col md:flex-row md:items-end gap-6">
          <div className="flex-1">
            <div className={`badge mb-4 ${netPos ? 'badge-green' : 'badge-red'}`}>
              {netPos ? '▲ Profitable' : '▼ Net Loss'}
            </div>
            <p className="text-text-secondary text-sm font-medium uppercase tracking-wider mb-2">
              Net Position — {stats?.period_name || '...'}
            </p>
            {loading ? (
              <Shimmer className="h-16 w-64" />
            ) : (
              <div className={`num text-6xl md:text-7xl font-black ${netPos ? 'text-green' : 'text-red'}`}>
                {netPos ? '+' : '-'}{fmt(Math.abs(net))}
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            {[
              { label: 'Total Income',  value: fmt(stats?.total_income ?? 0),  color: 'text-green' },
              { label: 'Total Expenses',value: fmt(stats?.total_expense ?? 0), color: 'text-red' },
            ].map((item) => (
              <div key={item.label} className="bg-white/5 border border-white/10 rounded-2xl p-4">
                <p className="text-white/50 text-xs mb-1">{item.label}</p>
                <p className={`num font-bold text-lg ${item.color}`}>{item.value}</p>
              </div>
            ))}
          </div>
        </div>
      </motion.div>

      {/* ── 4-stat row ────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-5">
        {statCards.map((c) => <StatCard key={c.label} {...c} loading={loading} />)}
      </div>

      {/* ── Charts + Side panels ───────────────────────────────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

        {/* Area Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="card p-6 xl:col-span-2"
        >
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="font-semibold">6-Month Performance</h3>
              <p className="text-text-muted text-xs mt-0.5">Historical Trends (Real Data)</p>
            </div>
            <div className="flex gap-4 text-xs">
              {[['Income','#10b981'],['Expenses','#f43f5e'],['Net','#6366f1']].map(([l,c]) => (
                <div key={l} className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ background: c }} />
                  <span className="text-text-secondary">{l}</span>
                </div>
              ))}
            </div>
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={stats?.trends || SAMPLE_TREND}>
              <defs>
                {[['green','#10b981'],['red','#f43f5e'],['brand','#6366f1']].map(([id,c]) => (
                  <linearGradient key={id} id={`grad-${id}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor={c} stopOpacity={0.2} />
                    <stop offset="95%" stopColor={c} stopOpacity={0} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="name" tick={{ fill: '#475569', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#475569', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => `${(v/1000).toFixed(0)}k`} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="income"   stroke="#10b981" strokeWidth={2} fill="url(#grad-green)" />
              <Area type="monotone" dataKey="expense" stroke="#f43f5e" strokeWidth={2} fill="url(#grad-red)" />
              <Area type="monotone" dataKey="net"      stroke="#6366f1" strokeWidth={2} fill="url(#grad-brand)" />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Side: Obligations */}
        <div className="space-y-5">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.28 }}
            className="card p-5 border-l-4 border-red/30"
          >
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <AlertTriangle size={16} className="text-red" /> Overdue Receivables
            </h3>
            <div className="space-y-4">
              {!stats?.overdue_receivables || stats.overdue_receivables.length === 0 ? (
                <p className="text-[10px] text-text-muted py-2 text-center">No overdue payments. Great!</p>
              ) : (
                stats.overdue_receivables.map((item: any, i: number) => (
                  <div key={i} className="flex justify-between items-start py-1.5 border-b border-white/5 last:border-0 border-dashed">
                    <div>
                      <p className="text-xs font-bold text-red-400">{item.client}</p>
                      <p className="text-[10px] text-text-secondary">{item.title}</p>
                      <div className="badge badge-red py-0 px-1.5 text-[9px] mt-1">{item.days_late} Days Late</div>
                    </div>
                    <span className="num text-sm font-black text-red-500">
                      {fmt(item.amount)}
                    </span>
                  </div>
                ))
              )}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="card p-5"
          >
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <Calendar size={16} className="text-brand" /> Upcoming Obligations
            </h3>
            <div className="space-y-4">
              {!stats?.obligations || stats.obligations.length === 0 ? (
                <p className="text-xs text-text-muted py-4 text-center">No obligations in next 30 days.</p>
              ) : (
                stats.obligations.map((item: any, i: number) => (
                  <div key={i} className="flex justify-between items-center py-1">
                    <div>
                      <p className="text-sm font-medium">{item.title}</p>
                      <p className="text-[10px] text-text-muted opacity-80 uppercase">Due: {new Date(item.date).toLocaleDateString()}</p>
                    </div>
                    <span className={`num text-sm font-bold ${item.type === 'receivable' ? 'text-green' : 'text-red'}`}>
                      {item.type === 'receivable' ? '+' : '-'}{fmt(item.amount)}
                    </span>
                  </div>
                ))
              )}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.35 }}
            className="card p-5"
          >
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <AlertTriangle size={16} className="text-amber" /> Bank Liquidity
            </h3>
            <div className="space-y-4">
              <p className="text-xs text-text-muted">Enter your current bank balance to calculate your cash runway weeks accurately.</p>
              <div className="space-y-2">
                 <input className="input py-2 text-sm w-full" type="number" value={balanceInput} onChange={e => setBalanceInput(e.target.value)} placeholder="Amount..." />
                 <button onClick={saveBalance} className="btn-primary w-full py-2 text-xs uppercase tracking-widest font-bold">Update Balance</button>
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      <AIConsultant />
    </div>
  )
}
