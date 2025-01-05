import { createApp } from 'vue'
import App from './App.vue'
import axios from 'axios'
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'

const app = createApp(App)

// 配置 axios 为全局属性
app.config.globalProperties.$http = axios

// 设置基础URL（可选）
// axios.defaults.baseURL = 'http://localhost:5000'

app.mount('#app')
