<template>
  <div class="key-value-config">
    <div 
      v-for="(value, key) in modelValue" 
      :key="key"
      class="key-value-item"
    >
      <div class="key-name">{{ key }}</div>
      <input 
        :value="value"
        @input="updateValue(key, $event.target.value)"
        class="mac-input"
        :placeholder="`${key}的值`"
        :disabled="disabled"
      >
      <button 
        type="button" 
        class="key-value-remove" 
        @click="removeItem(key)"
        :disabled="disabled"
      >×</button>
    </div>
    
    <div class="key-value-add" v-if="!disabled">
      <input 
        v-model="newItem.key"
        class="mac-input"
        :placeholder="keyPlaceholder"
      >
      <input 
        v-model="newItem.value"
        class="mac-input"
        :placeholder="valuePlaceholder"
      >
      <button 
        type="button" 
        class="mac-btn small" 
        @click="addItem"
      >{{ addButtonText }}</button>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits, reactive } from 'vue'
import message from '@/utils/message'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  },
  disabled: {
    type: Boolean,
    default: false
  },
  keyPlaceholder: {
    type: String,
    default: '键名'
  },
  valuePlaceholder: {
    type: String,
    default: '值'
  },
  addButtonText: {
    type: String,
    default: '添加'
  },
  keyRequiredMessage: {
    type: String,
    default: '请输入键名'
  }
})

const emit = defineEmits(['update:modelValue'])

const newItem = reactive({
  key: '',
  value: ''
})

// 更新值
const updateValue = (key, value) => {
  const updatedValue = { ...props.modelValue, [key]: value }
  emit('update:modelValue', updatedValue)
}

// 添加新项
const addItem = () => {
  if (!newItem.key) {
    message.warning(props.keyRequiredMessage)
    return
  }
  
  // 创建一个新对象以触发响应式更新
  const updatedValue = { ...props.modelValue, [newItem.key]: newItem.value }
  
  // 触发更新事件
  emit('update:modelValue', updatedValue)
  
  // 清空输入
  newItem.key = ''
  newItem.value = ''
}

// 移除项
const removeItem = (key) => {
  // 创建一个新对象以触发响应式更新
  const updatedValue = { ...props.modelValue }
  delete updatedValue[key]
  
  // 触发更新事件
  emit('update:modelValue', updatedValue)
}
</script>

<style scoped>
.key-value-config {
  display: flex;
  flex-direction: column;
  gap: 8px;
  border: 1px solid #E5E7EB;
  border-radius: 6px;
  padding: 12px;
  background: #F9FAFB;
}

.key-value-item {
  display: grid;
  grid-template-columns: 150px 1fr 30px;
  gap: 8px;
  align-items: center;
}

.key-name {
  font-weight: 500;
  font-size: 13px;
  color: #1C1C1E;
}

.key-value-remove {
  border: none;
  background: transparent;
  color: #6B7280;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  padding: 0;
}

.key-value-remove:hover:not(:disabled) {
  color: #DC2626;
}

.key-value-remove:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.key-value-add {
  display: grid;
  grid-template-columns: 150px 1fr auto;
  gap: 8px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #E5E7EB;
}

.mac-btn.small {
  height: 36px;
  padding: 0 12px;
  font-size: 12px;
  background: #F0F9FF;
  color: #0369A1;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.mac-btn.small:hover {
  background: #E0F2FE;
}

.mac-input {
  width: 100%;
  height: 36px;
  padding: 0 12px;
  border-radius: 6px;
  border: 1px solid #E5E7EB;
  background: #FFFFFF;
  color: #1C1C1E;
  font-size: 14px;
  transition: all 0.2s ease;
}

.mac-input:focus {
  outline: none;
  border-color: #007AFF;
  box-shadow: 0 0 0 2px rgba(0, 122, 255, 0.1);
}

.mac-input:disabled {
  background: #F3F4F6;
  cursor: not-allowed;
}
</style> 