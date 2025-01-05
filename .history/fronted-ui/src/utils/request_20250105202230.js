import axios from 'axios'
import message from './message'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000',
  timeout: 5000
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    console.log('Request:', {
      method: config.method,
      url: config.url,
      data: config.data
    })
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    console.log('Response:', {
      status: response.status,
      data: response.data
    })
    return response.data
  },
  error => {
    console.error('Response Error:', {
      status: error.response?.status,
      data: error.response?.data
    })
    message.error(error.response?.data?.error || '请求失败')
    return Promise.reject(error)
  }
)

export default service 