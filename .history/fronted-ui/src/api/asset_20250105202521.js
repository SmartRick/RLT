import request from '@/utils/request'

const BASE_URL = '/api/v1/assets'

export const assetApi = {
  /**
   * 获取资产列表
   */
  getAssets() {
    return request.get(BASE_URL)
  },

  /**
   * 创建资产
   */
  createAsset(data) {
    return request.post(BASE_URL, data)
  },

  /**
   * 更新资产
   */
  updateAsset(id, data) {
    return request.put(`${BASE_URL}/${id}`, data)
  },

  /**
   * 删除资产
   */
  deleteAsset(id) {
    return request.delete(`${BASE_URL}/${id}`)
  },

  /**
   * 验证资产能力
   */
  verifyCapabilities(id) {
    return request.post(`${BASE_URL}/${id}/verify`)
  }
} 