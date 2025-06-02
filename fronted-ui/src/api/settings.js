import request from '@/utils/request'
const BASE_URL = '/settings'

export const settingsApi = {
  /**
   * 获取设置
   * @returns {Promise<Object>} 系统设置
   */
  async getSettings() {
    return request.get(BASE_URL)
  },
  
  /**
   * 更新设置
   * @param {Object} data - 设置数据
   * @returns {Promise<Object>} 更新后的设置
   */
  async updateSettings(data) {
    return request.put(BASE_URL, data)
  }
} 