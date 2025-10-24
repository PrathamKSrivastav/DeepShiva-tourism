import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/api'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
})

// Fetch available personas
export const fetchPersonas = async () => {
  try {
    const response = await apiClient.get('/personas')
    return response.data
  } catch (error) {
    console.error('Error fetching personas:', error)
    throw error
  }
}

// Send chat message
export const sendChatMessage = async (message, persona, context = {}) => {
  try {
    const response = await apiClient.post('/chat', {
      message,
      persona,
      context
    })
    return response.data
  } catch (error) {
    console.error('Error sending chat message:', error)
    throw error
  }
}

// Fetch weather data
export const fetchWeather = async () => {
  try {
    const response = await apiClient.get('/mock/weather')
    return response.data
  } catch (error) {
    console.error('Error fetching weather:', error)
    throw error
  }
}

// Fetch crowd data
export const fetchCrowd = async () => {
  try {
    const response = await apiClient.get('/mock/crowd')
    return response.data
  } catch (error) {
    console.error('Error fetching crowd data:', error)
    throw error
  }
}

// Fetch festivals
export const fetchFestivals = async () => {
  try {
    const response = await apiClient.get('/mock/festivals')
    return response.data
  } catch (error) {
    console.error('Error fetching festivals:', error)
    throw error
  }
}

// Fetch emergency contacts
export const fetchEmergency = async () => {
  try {
    const response = await apiClient.get('/mock/emergency')
    return response.data
  } catch (error) {
    console.error('Error fetching emergency data:', error)
    throw error
  }
}

export default apiClient
