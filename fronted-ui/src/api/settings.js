import request from '@/utils/request'
const BASE_URL = '/settings'

export const settingsApi = {
  // 获取设置
  getSettings() {
    return request.get(BASE_URL)
  },
  
  // 更新设置
  updateSettings(data) {
    return request.put(BASE_URL, data)
  }
} 