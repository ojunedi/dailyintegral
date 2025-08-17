import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  // Get today's problem
  async getTodayProblem() {
    try {
      const response = await api.get('/problem');
      return response.data;
    } catch (error) {
      console.error('Error fetching problem:', error);
      throw new Error(
        error.response?.data?.error || 
        'Failed to fetch today\'s problem'
      );
    }
  },

  // Submit answer
  async submitAnswer(answer) {
    try {
      const response = await api.post('/submit', { answer });
      return response.data;
    } catch (error) {
      console.error('Error submitting answer:', error);
      throw new Error(
        error.response?.data?.error || 
        'Failed to submit answer'
      );
    }
  },

  // Health check
  async healthCheck() {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      console.error('API health check failed:', error);
      throw new Error('API is not available');
    }
  }
};