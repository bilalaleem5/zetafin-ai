import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Register from './pages/Register'
import Onboarding from './pages/Onboarding'
import Dashboard from './pages/Dashboard'
import Transactions from './pages/Transactions'
import Clients from './pages/Clients'
import Employees from './pages/Employees'
import Expenses from './pages/Expenses'
import Layout from './components/Layout'

const isAuth = () => !!localStorage.getItem('zetamize_token')

const Private = ({ children }: { children: React.ReactNode }) =>
  isAuth() ? <>{children}</> : <Navigate to="/login" replace />

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login"    element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/onboarding" element={<Private><Onboarding /></Private>} />
        <Route element={<Private><Layout /></Private>}>
          <Route path="/"            element={<Dashboard />} />
          <Route path="/transactions" element={<Transactions />} />
          <Route path="/clients"      element={<Clients />} />
          <Route path="/employees"    element={<Employees />} />
          <Route path="/expenses"     element={<Expenses />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
