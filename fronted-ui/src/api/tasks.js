import request from '@/utils/request'

const BASE_URL = '/tasks'

export const tasksApi = {
  // 获取任务列表
  getTasks(params) {
    return request.get(BASE_URL, { params })
  },
  
  // 创建任务
  createTask(data) {
    return request.post(BASE_URL, data)
  },
  
  // 获取任务详情
  getTaskById(id) {
    return request.get(`${BASE_URL}/${id}`)
  },
  
  // 更新任务
  updateTask(id, data) {
    return request.put(`${BASE_URL}/${id}`, data)
  },
  
  // 删除任务
  deleteTask(id) {
    return request.delete(`${BASE_URL}/${id}`)
  },
  
  // 上传图片
  uploadImages(taskId, formData) {
    return request.post(`${BASE_URL}/${taskId}/images`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 删除图片
  deleteImage(taskId, imageId) {
    return request.delete(`${BASE_URL}/${taskId}/images/${imageId}`)
  },
  
  // 开始标记
  startMarking(taskId) {
    return request.post(`${BASE_URL}/${taskId}/mark`)
  },
  
  // 开始训练
  startTraining(taskId) {
    return request.post(`${BASE_URL}/${taskId}/train`)
  },
  
  /**
   * 重启任务
   * @param {number|string} taskId - 任务ID
   * @returns {Promise<Object>} 任务信息
   */
  async restartTask(taskId) {
    const response = await request.post(`/tasks/${taskId}/restart`)
    return response.data
  },
  
  /**
   * 取消任务
   * @param {number|string} taskId - 任务ID
   * @returns {Promise<Object>} 任务信息
   */
  async cancelTask(taskId) {
    const response = await request.post(`/tasks/${taskId}/cancel`)
    return response
  }
} 