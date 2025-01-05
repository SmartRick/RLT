<template>
  <div class="tasks-container">
    <div class="mac-card">
      <h2>任务管理</h2>
      <p>任务管理内容</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'

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