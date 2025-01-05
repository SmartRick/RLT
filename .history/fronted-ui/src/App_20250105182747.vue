<template>
  <div class="app-background">
    <div class="blur-layer" :style="blurPosition"></div>
    <div class="gradient-layer"></div>
  </div>
  <app-layout />
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import AppLayout from '@/components/layout/AppLayout.vue'

// 视差效果状态
const blurPosition = ref({ transform: 'translate(0px, 0px)' })

// 处理鼠标移动
const handleMouseMove = (e) => {
  const moveX = (e.clientX - window.innerWidth / 2) * 0.01
  const moveY = (e.clientY - window.innerHeight / 2) * 0.01
  blurPosition.value = {
    transform: `translate(${moveX}px, ${moveY}px)`
  }
}

// 组件挂载时添加事件监听
onMounted(() => {
  window.addEventListener('mousemove', handleMouseMove)
  console.log('App component mounted')
})

// 组件卸载时移除事件监听
onUnmounted(() => {
  window.removeEventListener('mousemove', handleMouseMove)
})
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
  background: #f5f5f7;
  overflow: hidden;
}

.app-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: -1;
  overflow: hidden;
}

.blur-layer {
  position: absolute;
  top: -20px;
  left: -20px;
  right: -20px;
  bottom: -20px;
  background: 
    radial-gradient(circle at 30% 20%, rgba(121, 68, 154, 0.13), transparent 25%),
    radial-gradient(circle at 70% 65%, rgba(33, 150, 243, 0.13), transparent 25%),
    radial-gradient(circle at 20% 80%, rgba(234, 88, 12, 0.13), transparent 25%);
  filter: blur(30px);
  transition: transform 0.2s cubic-bezier(0.2, 0, 0.2, 1);
}

.gradient-layer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.95) 0%,
    rgba(255, 255, 255, 0.85) 100%
  );
  backdrop-filter: blur(20px);
}

/* Mac 风格的按钮样式 */
.mac-btn {
  background: linear-gradient(to bottom, rgba(255, 255, 255, 0.8) 0%, rgba(247, 247, 247, 0.8) 100%);
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 6px;
  padding: 8px 15px;
  font-size: 14px;
  color: #606266;
  cursor: pointer;
  transition: all 0.3s ease;
  backdrop-filter: blur(8px);
}

.mac-btn:hover {
  background: linear-gradient(to bottom, rgba(247, 247, 247, 0.9) 0%, rgba(240, 240, 240, 0.9) 100%);
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Mac 风格的卡片样式 */
.mac-card {
  background: rgba(255, 255, 255, 0.7);
  border-radius: 10px;
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.1),
    0 0 0 1px rgba(0, 0, 0, 0.05);
  padding: 20px;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
}

.mac-card:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 8px 24px rgba(0, 0, 0, 0.12),
    0 0 0 1px rgba(0, 0, 0, 0.05);
}
</style>
