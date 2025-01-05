import axios from 'axios'

const request = axios.create({
  baseURL: process.env.VUE_APP_API_URL || '/api/v1',
  timeout: 15000
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    // 在这里可以添加认证信息等
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    return response
  },
  error => {
    const { response } = error
    if (response && response.data) {
      const message = response.data.detail || response.data.message || '请求失败'
      // 这里可以集成全局错误提示
      console.error('响应错误:', message)
    } else {
      console.error('网络错误')
    }
    return Promise.reject(error)
  }
)

export default request 