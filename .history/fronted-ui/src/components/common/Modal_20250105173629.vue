<template>
  <transition name="modal">
    <div v-if="modelValue" class="modal-overlay">
      <div class="modal-wrapper mac-card" @click.stop>
        <div class="modal-header">
          <h3>{{ title }}</h3>
          <button class="close-btn" @click="close">
            <XMarkIcon class="close-icon" />
          </button>
        </div>
        
        <div class="modal-body">
          <slot name="body"></slot>
        </div>
        
        <div class="modal-footer">
          <slot name="footer">
            <button class="mac-btn" @click="close">取消</button>
            <button class="mac-btn primary" @click="$emit('confirm')">确认</button>
          </slot>
        </div>
      </div>
    </div>
  </transition>
</template>

<script>
import { XMarkIcon } from '@heroicons/vue/24/outline'

export default {
  name: 'BaseModal',
  components: {
    XMarkIcon
  },
  props: {
    modelValue: Boolean,
    title: String
  },
  emits: ['update:modelValue'],
  methods: {
    close() {
      this.$emit('update:modelValue', false)
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-wrapper {
  width: 500px;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.95);
}

.modal-header {
  padding: 16px 24px;
  border-bottom: 1px solid #E5E7EB;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-header h3 {
  font-size: 18px;
  font-weight: 600;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  transition: all var(--transition-speed);
}

.close-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #333;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #E5E7EB;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 动画效果 */
.modal-enter-active,
.modal-leave-active {
  transition: opacity var(--transition-speed);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-wrapper,
.modal-leave-active .modal-wrapper {
  transition: transform var(--transition-speed);
}

.modal-enter-from .modal-wrapper,
.modal-leave-to .modal-wrapper {
  transform: scale(0.95);
}

.close-icon {
  width: 20px;
  height: 20px;
}
</style> 