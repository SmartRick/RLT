<template>
  <div class="tasks-container">
    <div class="mac-card">
      <h2 class="page-title">任务管理</h2>
      <div class="placeholder-content">
        <div class="placeholder-icon">
          <ChartBarIcon class="icon" />
        </div>
        <p>任务管理页面开发中...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ChartBarIcon } from '@heroicons/vue/24/outline'
</script>

<style scoped>
.tasks-container {
  height: 100%;
}

.page-title {
  font-size: 24px;
  font-weight: 500;
  color: #1c1c1e;
  margin-bottom: 20px;
}

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #8e8e93;
}

.placeholder-icon {
  margin-bottom: 16px;
}

.icon {
  width: 48px;
  height: 48px;
}
</style> 