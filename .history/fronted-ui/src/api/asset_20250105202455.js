import request from '@/utils/request'

export const assetApi = {
  /**
   * 获取资产列表
   * @returns {Promise<Array>} 资产列表
   */
  getAssets() {
    return request.get('/assets/')
  },

  /**
   * 创建资产
   * @param {Object} data - 资产数据
   * @returns {Promise<Object>} 创建的资产
   */
  createAsset(data) {
    return request.post('/assets/', data)
  },

  /**
   * 更新资产
   * @param {number|string} id - 资产ID
   * @param {Object} data - 更新数据
   * @returns {Promise<Object>} 更新后的资产
   */
  updateAsset(id, data) {
    return request.put(`/assets/${id}/`, data)
  },

  /**
   * 删除资产
   * @param {number|string} id - 资产ID
   * @returns {Promise<void>}
   */
  deleteAsset(id) {
    return request.delete(`/assets/${id}/`)
  },

  /**
   * 验证资产能力
   * @param {number|string} id - 资产ID
   * @returns {Promise<Object>} 验证结果
   */
  verifyCapabilities(id) {
    return request.post(`/assets/${id}/verify/`)
  }
} 