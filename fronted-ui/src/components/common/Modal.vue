<template>
  <transition name="modal-backdrop">
    <div v-if="modelValue" class="modal-overlay" @click="close">
      <transition name="modal">
        <div class="modal-wrapper mac-card" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">{{ title }}</h3>
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
      </transition>
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
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(5px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-wrapper {
  width: 650px;
  max-width: 90vw;
  max-height: 85vh;
  margin: var(--spacing-6);
  background: var(--background-secondary);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.modal-header {
  padding: var(--spacing-4) var(--spacing-6);
  border-bottom: 1px solid var(--border-color-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.close-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  transition: all var(--transition-speed);
}

.close-btn:hover {
  background: var(--background-tertiary);
  color: var(--text-primary);
}

.close-icon {
  width: 20px;
  height: 20px;
}

.modal-body {
  padding: var(--spacing-6);
  overflow-y: auto;
}

.modal-footer {
  padding: var(--spacing-4) var(--spacing-6);
  border-top: 1px solid var(--border-color-light);
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-3);
}

/* 动画 */
.modal-backdrop-enter-active,
.modal-backdrop-leave-active {
  transition: opacity var(--transition-speed);
}

.modal-backdrop-enter-from,
.modal-backdrop-leave-to {
  opacity: 0;
}

.modal-enter-active,
.modal-leave-active {
  transition: all var(--transition-speed);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
  transform: scale(0.95);
}
</style> 