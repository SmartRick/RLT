import request from '@/utils/request'

const BASE_URL = '/assets'

export const assetApi = {
  /**
   * 获取资产列表
   * @returns {Promise<Array>} 资产列表
   */
  getAssets() {
    return request.get(BASE_URL)
  },

  /**
   * 创建资产
   * @param {Object} data - 资产数据
   * @returns {Promise<Object>} 创建的资产
   */
  createAsset(data) {
    return request.post(BASE_URL, data)
  },

  /**
   * 更新资产
   * @param {number|string} id - 资产ID
   * @param {Object} data - 更新数据
   * @returns {Promise<Object>} 更新后的资产
   */
  updateAsset(id, data) {
    return request.put(`${BASE_URL}/${id}`, data)
  },

  /**
   * 删除资产
   * @param {number|string} id - 资产ID
   * @returns {Promise<void>}
   */
  deleteAsset(id) {
    return request.delete(`${BASE_URL}/${id}`)
  },

  /**
   * 验证资产能力
   * @param {number|string} id - 资产ID
   * @returns {Promise<Object>} 验证结果
   */
  verifyCapabilities(id) {
    return request.post(`${BASE_URL}/${id}/verify`)
  },

  async verifySshConnection(data) {
    const response = await request.post('/api/assets/verify-ssh', data)
    return response.data
  }
} 