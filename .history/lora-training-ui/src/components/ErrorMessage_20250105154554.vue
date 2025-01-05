<template>
  <transition name="fade">
    <div v-if="message" class="error-message">
      <span class="error-icon">⚠️</span>
      <span class="error-text">{{ message }}</span>
      <button class="close-error" @click="$emit('close')">&times;</button>
    </div>
  </transition>
</template>

<script>
export default {
  name: 'ErrorMessage',
  props: {
    message: String
  }
}
</script>

<style lang="scss" scoped>
.error-message {
  background: rgba(255, 59, 48, 0.1);
  color: var(--error-color);
  padding: 12px 16px;
  border-radius: var(--border-radius);
  margin: 10px 0;
  display: flex;
  align-items: center;
  gap: 10px;
  
  .error-icon {
    font-size: 1.2em;
  }
  
  .error-text {
    flex: 1;
  }
  
  .close-error {
    background: none;
    border: none;
    color: var(--error-color);
    cursor: pointer;
    font-size: 1.2em;
    padding: 0 4px;
    
    &:hover {
      opacity: 0.8;
    }
  }
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style> 