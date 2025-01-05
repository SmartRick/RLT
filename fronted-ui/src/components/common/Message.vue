<template>
  <transition name="message-fade">
    <div v-if="visible" 
         class="message-container"
         :class="type">
      <component :is="iconComponent" 
                class="message-icon" 
                v-if="iconComponent" />
      <span class="message-content">{{ content }}</span>
    </div>
  </transition>
</template>

<script setup>
import { defineProps, defineExpose, defineComponent } from 'vue'
import { ref, computed } from 'vue'
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  XCircleIcon,
  InformationCircleIcon
} from '@heroicons/vue/24/outline'

defineComponent({
  name: 'SystemMessage'
})

/**
 * @typedef {'success' | 'warning' | 'error' | 'info'} MessageType
 */

const props = defineProps({
  content: {
    type: String,
    required: true
  },
  type: {
    type: String,
    default: 'info'
  },
  duration: {
    type: Number,
    default: 3000
  }
})

const visible = ref(false)

const iconComponent = computed(() => {
  const iconMap = {
    success: CheckCircleIcon,
    warning: ExclamationCircleIcon,
    error: XCircleIcon,
    info: InformationCircleIcon
  }
  return iconMap[props.type]
})

/**
 * 显示消息
 */
const show = () => {
  visible.value = true
  if (props.duration > 0) {
    setTimeout(() => {
      visible.value = false
    }, props.duration)
  }
}

defineExpose({
  show
})
</script>

<style scoped>
.message-container {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  display: flex;
  align-items: center;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  background: white;
  transition: all 0.3s ease;
}

.message-icon {
  width: 20px;
  height: 20px;
  margin-right: 8px;
}

.message-container.success {
  background: #F0FDF4;
  border: 1px solid #BBF7D0;
  color: #166534;
}

.message-container.success .message-icon {
  color: #16A34A;
}

.message-container.warning {
  background: #FFFBEB;
  border: 1px solid #FEF3C7;
  color: #92400E;
}

.message-container.warning .message-icon {
  color: #D97706;
}

.message-container.error {
  background: #FEF2F2;
  border: 1px solid #FECACA;
  color: #991B1B;
}

.message-container.error .message-icon {
  color: #DC2626;
}

.message-container.info {
  background: #EFF6FF;
  border: 1px solid #BFDBFE;
  color: #1E40AF;
}

.message-container.info .message-icon {
  color: #3B82F6;
}

.message-fade-enter-active,
.message-fade-leave-active {
  transition: all 0.3s ease;
}

.message-fade-enter-from,
.message-fade-leave-to {
  opacity: 0;
  transform: translate(-50%, -20px);
}
</style> 