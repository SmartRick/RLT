import axios from 'axios'

export const settingsApi = {
  getSettings() {
    return axios.get('/api/v1/settings/')
  },

  updateSettings(data) {
    return axios.put('/api/v1/settings/', data)
  },

  getSystemInfo() {
    return axios.get('/api/v1/system/info')
  }
} 