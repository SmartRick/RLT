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
})

// 组件卸载时移除事件监听
onUnmounted(() => {
  window.removeEventListener('mousemove', handleMouseMove)
})
</script>

<style>
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
</style>
