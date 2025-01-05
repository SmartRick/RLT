<template>
  <div class="tasks-container">
    <div class="mac-card">
      <h2>任务管理</h2>
      <p>任务管理内容</p>
    </div>
  </div>
</template>

<script setup>
import { defineComponent, onMounted } from 'vue'

// 定义组件名称
defineComponent({
  name: 'TaskManagerView'
})

onMounted(() => {
  console.log('Tasks component mounted')
})
</script>

<style scoped>
.tasks-container {
  height: 100%;
  width: 100%;
  padding: 20px;
}
</style> 