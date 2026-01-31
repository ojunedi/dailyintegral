import axios from 'axios'

const API_BASE_URL = '/api'

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
  }
}
