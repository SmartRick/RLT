import request from '@/utils/request'

export const trainingApi = {
  // 训练素材相关
  listMaterials() {
    return request.get('/materials/')
  },

  createMaterial(data) {
    return request.post('/materials/', data)
  },

  updateMaterial(id, data) {
    return request.put(`/materials/${id}`, data)
  },

  deleteMaterial(id) {
    return request.delete(`/materials/${id}`)
  },

  uploadMaterialFiles(materialId, formData) {
    return request.post(`/materials/${materialId}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 训练任务相关
  listTasks() {
    return request.get('/tasks/')
  },

  createTask(data) {
    return request.post('/tasks/', data)
  },

  updateTask(id, data) {
    return request.put(`/tasks/${id}`, data)
  },

  deleteTask(id) {
    return request.delete(`/tasks/${id}`)
  }
} 