import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://140.245.219.55',
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
