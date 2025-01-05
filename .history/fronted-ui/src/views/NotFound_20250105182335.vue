<template>
  <div class="not-found-container">
    <div class="mac-card">
      <div class="error-content">
        <h1 class="error-code">404</h1>
        <p class="error-message">页面未找到</p>
        <router-link to="/" class="mac-btn">
          返回首页
        </router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.not-found-container {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.error-content {
  text-align: center;
  padding: 40px;
}

.error-code {
  font-size: 72px;
  font-weight: 200;
  color: #1c1c1e;
  margin-bottom: 16px;
}

.error-message {
  font-size: 18px;
  color: #8e8e93;
  margin-bottom: 24px;
}
</style> 