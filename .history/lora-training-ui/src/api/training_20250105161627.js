import axios from 'axios'

export const trainingApi = {
  // 训练素材相关
  listMaterials() {
    return axios.get('/api/v1/materials/')
  },

  createMaterial(data) {
    return axios.post('/api/v1/materials/', data)
  },

  updateMaterial(id, data) {
    return axios.put(`/api/v1/materials/${id}`, data)
  },

  deleteMaterial(id) {
    return axios.delete(`/api/v1/materials/${id}`)
  },

  uploadMaterialFiles(materialId, formData) {
    return axios.post(`/api/v1/materials/${materialId}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 训练任务相关
  listTasks() {
    return axios.get('/api/v1/tasks/')
  },

  createTask(data) {
    return axios.post('/api/v1/tasks/', data)
  },

  updateTask(id, data) {
    return axios.put(`/api/v1/tasks/${id}`, data)
  },

  deleteTask(id) {
    return axios.delete(`/api/v1/tasks/${id}`)
  }
} 