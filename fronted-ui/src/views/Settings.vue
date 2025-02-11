<template>
  <div class="settings-container">
    <div class="mac-card settings-card">
      <h2 class="settings-title">系统设置</h2>
      
      <form @submit.prevent="handleSubmit" class="settings-form">
        <div class="form-group">
          <label>源文件目录</label>
          <input 
            v-model="form.source_dir"
            class="mac-input"
            placeholder="请输入源文件目录路径"
          >
        </div>
        
        <div class="form-group">
          <label>Lora输出目录</label>
          <input 
            v-model="form.lora_output_path"
            class="mac-input"
            placeholder="请输入Lora输出目录路径"
          >
        </div>
        
        <div class="form-group">
          <label>调度间隔(分钟)</label>
          <input 
            v-model.number="form.scheduling_minute"
            type="number"
            class="mac-input"
            min="1"
            max="60"
          >
        </div>
        
        <div class="form-group">
          <label>标记文件目录</label>
          <input 
            v-model="form.mark_pan_dir"
            class="mac-input"
            placeholder="请输入标记文件目录路径"
          >
        </div>
        
        <div class="form-group">
          <label>Lora上传目录</label>
          <input 
            v-model="form.lora_pan_upload_dir"
            class="mac-input"
            placeholder="请输入Lora上传目录路径"
          >
        </div>
        
        <div class="form-actions">
          <button 
            type="submit" 
            class="mac-btn primary"
            :disabled="isSubmitting"
          >
            {{ isSubmitting ? '保存中...' : '保存设置' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { settingsApi } from '@/api/settings'
import message from '@/utils/message'

const form = ref({
  source_dir: '',
  lora_output_path: '',
  scheduling_minute: 5,
  mark_pan_dir: '',
  lora_pan_upload_dir: ''
})

const isSubmitting = ref(false)

// 获取设置
const fetchSettings = async () => {
  try {
    const data = await settingsApi.getSettings()
    form.value = data
  } catch (error) {
    message.error('获取设置失败')
  }
}

// 提交设置
const handleSubmit = async () => {
  try {
    isSubmitting.value = true
    await settingsApi.updateSettings(form.value)
    message.success('设置已保存')
  } catch (error) {
    message.error('保存设置失败')
  } finally {
    isSubmitting.value = false
  }
}

onMounted(() => {
  fetchSettings()
})
</script>

<style scoped>
.settings-container {
  padding: 24px;
  height: 100%;
  overflow: auto;
}

.settings-card {
  max-width: 800px;
  margin: 0 auto;
}

.settings-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 24px;
  color: var(--text-primary);
}

.settings-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  color: var(--text-secondary);
}

.form-actions {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style> 