import Vue from 'vue'
import App from './App.vue'
import axios from 'axios'

// 配置 axios
Vue.prototype.$http = axios

// 设置基础URL（可选）
// axios.defaults.baseURL = 'http://localhost:5000'

Vue.config.productionTip = false

new Vue({
  render: h => h(App)
}).$mount('#app')
