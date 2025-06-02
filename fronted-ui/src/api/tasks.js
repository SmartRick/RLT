import request from '@/utils/request'

const BASE_URL = '/tasks'

export const tasksApi = {
  // 获取任务列表
  async getTasks(params) {
    return request.get(BASE_URL, { params })
  },
  
  // 创建任务
  async createTask(data) {
    return request.post(BASE_URL, data)
  },
  
  // 获取任务详情
  async getTaskById(id) {
    return request.get(`${BASE_URL}/${id}`)
  },
  
  // 更新任务
  async updateTask(id, data) {
    return request.put(`${BASE_URL}/${id}`, data)
  },
  
  // 删除任务
  async deleteTask(id) {
    return request.delete(`${BASE_URL}/${id}`)
  },
  
  // 上传图片
  async uploadImages(taskId, formData) {
    return request.post(`${BASE_URL}/${taskId}/images`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 删除图片
  async deleteImage(taskId, imageId) {
    return request.delete(`${BASE_URL}/${taskId}/images/${imageId}`)
  },
  
  // 开始标记
  async startMarking(taskId) {
    return request.post(`${BASE_URL}/${taskId}/mark`)
  },
  
  // 开始训练
  async startTraining(taskId) {
    return request.post(`${BASE_URL}/${taskId}/train`)
  },
  
  /**
   * 重启任务
   * @param {number|string} taskId - 任务ID
   * @returns {Promise<Object>} 任务信息
   */
  async restartTask(taskId) {
    return request.post(`${BASE_URL}/${taskId}/restart`)
  },
  
  /**
   * 取消任务
   * @param {number|string} taskId - 任务ID
   * @returns {Promise<Object>} 任务信息
   */
  async cancelTask(taskId) {
    return request.post(`${BASE_URL}/${taskId}/cancel`)
  },
  
  /**
   * 获取任务状态
   * @param {number|string} taskId - 任务ID
   * @returns {Promise<Object>} 任务状态信息
   */
  async getTaskStatus(taskId) {
    return request.get(`${BASE_URL}/${taskId}/status`)
  }
} 