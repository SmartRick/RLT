<template>
  <div v-if="message" class="error-message">
    <div class="error-content">
      <span class="error-icon">⚠️</span>
      <span class="error-text">{{ message }}</span>
    </div>
    <button class="close-btn" @click="$emit('close')">×</button>
  </div>
</template>

<script>
export default {
  name: 'ErrorMessage',
  props: {
    message: {
      type: String,
      required: true
    }
  },
  emits: ['close']
}
</script>

<style lang="scss" scoped>
.error-message {
  background: var(--error-color);
  color: white;
  padding: 12px 16px;
  border-radius: var(--border-radius);
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  animation: slideIn 0.3s ease-out;

  .error-content {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .error-icon {
    font-size: 1.2em;
  }

  .close-btn {
    background: none;
    border: none;
    color: white;
    font-size: 1.2em;
    cursor: pointer;
    padding: 0 5px;
    opacity: 0.8;

    &:hover {
      opacity: 1;
    }
  }
}

@keyframes slideIn {
  from {
    transform: translateY(-100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
</style> 