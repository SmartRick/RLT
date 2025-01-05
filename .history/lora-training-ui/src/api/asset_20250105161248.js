import axios from 'axios'

export const assetApi = {
  list() {
    return axios.get('/api/v1/assets/')
  },
  
  create(data) {
    return axios.post('/api/v1/assets/', data)
  },
  
  update(id, data) {
    return axios.put(`/api/v1/assets/${id}`, data)
  },
  
  delete(id) {
    return axios.delete(`/api/v1/assets/${id}`)
  }
} 