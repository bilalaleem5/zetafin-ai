import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MessageSquare, X, Send, Bot, Sparkles, User } from 'lucide-react'
import api from '../api'

export default function AIConsultant() {
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [messages, setMessages] = useState<any[]>([
    { role: 'assistant', content: 'Hello CEO! I am your financial consultant. How can I help you today?' }
  ])
  const [loading, setLoading] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }, [messages])

  const handleSend = async () => {
    if (!query.trim() || loading) return
    const userMsg = query.trim()
    setQuery('')
    setMessages(prev => [...prev, { role: 'user', content: userMsg }])
    setLoading(true)

    try {
      const { data } = await api.post('/ai/query', { query: userMsg })
      setMessages(prev => [...prev, { role: 'assistant', content: data.answer }])
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I am having trouble connecting to the brain. Please try again.' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {/* Floating Button */}
      <button 
        onClick={() => setIsOpen(true)}
        className="fixed bottom-8 right-8 p-4 rounded-full bg-brand text-white shadow-xl hover:scale-110 active:scale-95 transition-all z-50 group overflow-hidden"
      >
        <div className="absolute inset-0 bg-gradient-to-tr from-white/0 to-white/20 group-hover:translate-x-full transition-transform duration-500" />
        <MessageSquare size={24} />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 100, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 100, scale: 0.9 }}
            className="fixed bottom-24 right-8 w-[380px] h-[500px] glass rounded-3xl shadow-2xl flex flex-col z-50 border border-white/20"
          >
            {/* Header */}
            <div className="p-4 border-b border-white/10 flex justify-between items-center bg-brand/10 rounded-t-3xl">
              <div className="flex items-center gap-2 text-brand">
                <Sparkles size={18} />
                <span className="font-bold text-sm">ZetaFin AI Consultant</span>
              </div>
              <button onClick={() => setIsOpen(false)} className="text-text-muted hover:text-white">
                <X size={18} />
              </button>
            </div>

            {/* Messages */}
            <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
              {messages.map((m, i) => (
                <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[85%] p-3 rounded-2xl text-xs leading-relaxed ${
                    m.role === 'user' 
                      ? 'bg-brand text-white rounded-tr-none' 
                      : 'bg-white/5 border border-white/10 rounded-tl-none'
                  }`}>
                    <div className="flex items-center gap-1.5 mb-1 opacity-50">
                      {m.role === 'user' ? <User size={10} /> : <Bot size={10} />}
                      <span className="font-bold uppercase tracking-tighter">
                        {m.role === 'user' ? 'You' : 'ZetaFin AI'}
                      </span>
                    </div>
                    {m.content}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-white/5 border border-white/10 p-3 rounded-2xl rounded-tl-none">
                    <div className="flex gap-1">
                      <div className="w-1.5 h-1.5 bg-brand rounded-full animate-bounce" />
                      <div className="w-1.5 h-1.5 bg-brand rounded-full animate-bounce [animation-delay:0.2s]" />
                      <div className="w-1.5 h-1.5 bg-brand rounded-full animate-bounce [animation-delay:0.4s]" />
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Input */}
            <div className="p-4 border-t border-white/10">
              <div className="relative">
                <input 
                  autoFocus
                  className="input w-full pr-12 py-3 text-xs" 
                  placeholder="Ask about burn rate, runway, or budgets..." 
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSend()}
                />
                <button 
                  onClick={handleSend}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-brand hover:scale-110 active:scale-95 transition-transform"
                >
                  <Send size={16} />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
