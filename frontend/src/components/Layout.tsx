import { useState } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { 
  LayoutDashboard, ArrowLeftRight, Users, UserCheck, 
  LogOut, Menu, MessageSquare, Bell, Store
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

const NAV = [
  { to: '/',            label: 'Dashboard',    icon: LayoutDashboard },
  { to: '/transactions',label: 'Transactions', icon: ArrowLeftRight },
  { to: '/clients',     label: 'Clients',      icon: Users },
  { to: '/employees',   label: 'Team',         icon: UserCheck },
  { to: '/expenses',    label: 'Expenses',     icon: ArrowLeftRight },
  { to: '/vendors',     label: 'Vendors',      icon: Store },
]

export default function Layout() {
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()

  const logout = () => {
    localStorage.removeItem('zetamize_token')
    navigate('/login')
  }

  const Sidebar = () => (
    <aside className="flex flex-col h-full w-64 bg-bg-surface border-r border-border p-5">
      {/* Logo */}
      <div className="flex items-center gap-3 mb-10 px-1">
        <img src="/logo.png" alt="ZetaFin AI" className="h-32 object-contain drop-shadow" />
      </div>

      {/* Nav Items */}
      <nav className="flex-1 space-y-1">
        <p className="text-text-muted text-xs font-semibold uppercase tracking-wider px-3 mb-3">Menu</p>
        {NAV.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `nav-link ${isActive ? 'active' : ''}`
            }
            onClick={() => setOpen(false)}
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* WhatsApp hint */}
      <div className="card p-4 mb-4 space-y-2">
        <div className="flex items-center gap-2">
          <MessageSquare size={15} className="text-green" />
          <span className="text-xs font-semibold text-text-primary">WhatsApp Bot Active</span>
        </div>
        <code className="text-xs text-text-muted block leading-relaxed">
          in 50000 Ali March-inv<br/>
          ex 8000 rent Office<br/>
          summary
        </code>
      </div>

      {/* Logout */}
      <button onClick={logout} className="nav-link w-full text-red hover:text-red hover:bg-red/5">
        <LogOut size={18} /> Sign Out
      </button>
    </aside>
  )

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base">
      {/* Desktop sidebar */}
      <div className="hidden md:flex flex-shrink-0">
        <Sidebar />
      </div>

      {/* Mobile sidebar drawer */}
      <AnimatePresence>
        {open && (
          <>
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/60 z-40 md:hidden"
              onClick={() => setOpen(false)}
            />
            <motion.div
              initial={{ x: -280 }} animate={{ x: 0 }} exit={{ x: -280 }}
              transition={{ type: 'spring', damping: 28, stiffness: 280 }}
              className="fixed left-0 top-0 bottom-0 z-50 md:hidden"
            >
              <Sidebar />
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top bar */}
        <header className="flex items-center justify-between px-6 py-4 border-b border-border bg-bg-surface flex-shrink-0">
          <button className="md:hidden" onClick={() => setOpen(true)}>
            <Menu size={22} />
          </button>
          <div className="hidden md:block" />
          <div className="flex items-center gap-3">
            <button className="relative p-2 rounded-xl hover:bg-white/5 transition-colors">
              <Bell size={18} className="text-text-secondary" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-brand rounded-full" />
            </button>
            <div className="w-9 h-9 rounded-xl bg-brand/20 border border-brand/30 flex items-center justify-center">
              <span className="text-brand font-bold text-sm">B</span>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
