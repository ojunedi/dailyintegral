import axios from 'axios'
import { supabase } from './supabase'

const API_BASE_URL = '/api'

const authAxios = axios.create({ baseURL: API_BASE_URL })

// Attach JWT to authenticated requests
authAxios.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession()
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`
  }
  return config
})

export const apiService = {
  async getTodayProblem() {
    try {
      const response = await axios.get(`${API_BASE_URL}/problem`)
      return response.data
    } catch (error) {
      console.error('Error fetching problem:', error)
      throw new Error(error.response?.data?.error || 'Failed to fetch problem')
    }
  },

  async submitAnswer(answer, problem) {
    try {
      const response = await axios.post(`${API_BASE_URL}/submit`, {
        answer: answer,
        problem: problem
      })
      return response.data
    } catch (error) {
      console.error('Error submitting answer:', error)
      throw new Error(error.response?.data?.error || 'Failed to submit answer')
    }
  },

  async healthCheck() {
    try {
      const response = await axios.get(`${API_BASE_URL}/health`)
      return response.data
    } catch (error) {
      console.error('Health check failed:', error)
      throw new Error('API health check failed')
    }
  },

  async saveProgress(entry) {
    const response = await authAxios.post('/progress', entry)
    return response.data
  },

  async getProgress() {
    const response = await authAxios.get('/progress')
    return response.data
  },

  async syncProgress(entries) {
    const response = await authAxios.post('/progress/sync', { entries })
    return response.data
  },
}
