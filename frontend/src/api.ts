import axios from 'axios'

const isProd = import.meta.env.MODE === 'production'
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || (isProd ? 'https://zetafin-ai.onrender.com' : 'http://localhost:8000'),
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('zetamize_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('zetamize_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
