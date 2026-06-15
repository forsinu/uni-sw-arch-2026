import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(null)
  const isAuthenticated = computed(() => !!token.value)

  const login = async (email, password) => {
    try {
      const response = await api.post('/v1/auth/login', {
        email,
        password
      })

      console.log('Login response:', response.data)
      token.value = response.data.accessToken

      try {
        const decoded = JSON.parse(atob(response.data.accessToken.split('.')[1]))
        console.log('Decoded token:', decoded)
        user.value = {
          id: decoded.sub,
          email: email,
          role: decoded.role,
          federationId: decoded.fed
        }
      } catch (decodeError) {
        console.error('Error decoding token:', decodeError)
        user.value = {
          id: null,
          email: email,
          role: null,
          federationId: null
        }
      }

      return true
    } catch (error) {
      console.error('Login error:', error)
      token.value = null
      user.value = null
      throw error
    }
  }

  const register = async (email, password) => {
    try {
      await api.post('/v1/auth/register', {
        email,
        password
      })
      return true
    } catch (error) {
      throw error
    }
  }

  const logout = () => {
    token.value = null
    user.value = null
  }

  const setToken = (newToken) => {
    token.value = newToken
  }

  return {
    user,
    token,
    isAuthenticated,
    login,
    register,
    logout,
    setToken
  }
})
