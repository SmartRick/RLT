import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './assets/styles/global.css'
import '@fortawesome/fontawesome-free/css/all.css'

// 创建工具函数
import { formatDate } from './utils/date'

const app = createApp(App)

// 注册全局方法
app.config.globalProperties.$formatDate = formatDate

app.use(router)
app.mount('#app')
