<template>
  <app-layout />
</template>

<script>
import AppLayout from '@/components/layout/AppLayout.vue'

export default {
  name: 'App',
  components: {
    AppLayout
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
}

/* Mac 风格的按钮样式 */
.mac-btn {
  background: linear-gradient(to bottom, #ffffff 0%, #f7f7f7 100%);
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  padding: 8px 15px;
  font-size: 14px;
  color: #606266;
  cursor: pointer;
  transition: all 0.3s ease;
}

.mac-btn:hover {
  background: linear-gradient(to bottom, #f7f7f7 0%, #f0f0f0 100%);
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Mac 风格的卡片样式 */
.mac-card {
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
  padding: 20px;
  transition: all 0.3s ease;
}

.mac-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px 0 rgba(0,0,0,0.15);
}
</style>
