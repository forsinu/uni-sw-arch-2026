import axios from 'axios'

// Durante lo sviluppo usa il proxy di Vite, in produzione usa l'URL completo
const API_BASE_URL = import.meta.env.DEV ? '/api' : (import.meta.env.VITE_API_URL || 'http://localhost:8000/api')

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true
})

api.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        await api.get('/v1/auth/refresh')
        return api(originalRequest)
      } catch (refreshError) {
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default api
