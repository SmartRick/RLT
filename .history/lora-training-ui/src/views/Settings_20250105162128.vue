<template>
  <div class="settings-view">
    <div class="settings-section">
      <h2>系统配置</h2>
      <form class="settings-form" @submit.prevent="saveSettings">
        <div class="form-group">
          <label>源文件目录</label>
          <input 
            type="text" 
            v-model="form.source_dir"
            placeholder="训练数据源文件目录"
          >
          <small>用于存放训练数据的目录路径</small>
        </div>

        <div class="form-group">
          <label>Lora输出路径</label>
          <input 
            type="text" 
            v-model="form.lora_output_path"
            placeholder="训练完成的Lora模型输出路径"
          >
          <small>训练完成后的模型文件存放路径</small>
        </div>

        <div class="form-group">
          <label>定时检查间隔（分钟）</label>
          <input 
            type="number" 
            v-model="form.scheduling_minute"
            min="1"
            step="1"
          >
          <small>系统自动检查任务状态的时间间隔</small>
        </div>

        <div class="form-group">
          <label>云盘标记文件目录</label>
          <input 
            type="text" 
            v-model="form.mark_pan_dir"
            placeholder="/loraFile/mark"
          >
          <small>用于存放标记文件的云盘目录</small>
        </div>

        <div class="form-group">
          <label>云盘Lora上传目录</label>
          <input 
            type="text" 
            v-model="form.lora_pan_upload_dir"
            placeholder="/loraFile/lora"
          >
          <small>训练完成的模型文件上传到云盘的目录</small>
        </div>

        <div class="form-actions">
          <button 
            type="submit" 
            class="save-btn"
            :disabled="!hasChanges || saving"
          >
            {{ saving ? '保存中...' : '保存更改' }}
          </button>
          <button 
            type="button" 
            class="reset-btn"
            @click="resetForm"
            :disabled="!hasChanges || saving"
          >
            重置
          </button>
        </div>
      </form>
    </div>

    <div class="settings-section">
      <h2>系统信息</h2>
      <div class="info-grid">
        <div class="info-item">
          <strong>版本:</strong>
          <span>{{ systemInfo.version }}</span>
        </div>
        <div class="info-item">
          <strong>运行时间:</strong>
          <span>{{ systemInfo.uptime }}</span>
        </div>
        <div class="info-item">
          <strong>CPU使用率:</strong>
          <span>{{ systemInfo.cpu_usage }}%</span>
        </div>
        <div class="info-item">
          <strong>内存使用:</strong>
          <span>{{ systemInfo.memory_usage }}</span>
        </div>
        <div class="info-item">
          <strong>磁盘使用:</strong>
          <span>{{ systemInfo.disk_usage }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed } from 'vue'
import { settingsApi } from '@/api/settings'

export default {
  name: 'Settings',
  setup() {
    const originalSettings = ref({})
    const saving = ref(false)
    const systemInfo = ref({
      version: '',
      uptime: '',
      cpu_usage: 0,
      memory_usage: '',
      disk_usage: ''
    })

    const form = reactive({
      source_dir: '',
      lora_output_path: '',
      scheduling_minute: 5,
      mark_pan_dir: '',
      lora_pan_upload_dir: ''
    })

    const hasChanges = computed(() => {
      return Object.keys(form).some(key => 
        form[key] !== originalSettings.value[key]
      )
    })

    const loadSettings = async () => {
      try {
        const response = await settingsApi.getSettings()
        Object.assign(form, response.data)
        originalSettings.value = { ...response.data }
      } catch (error) {
        console.error('加载设置失败:', error)
      }
    }

    const loadSystemInfo = async () => {
      try {
        const response = await settingsApi.getSystemInfo()
        systemInfo.value = response.data
      } catch (error) {
        console.error('加载系统信息失败:', error)
      }
    }

    const saveSettings = async () => {
      saving.value = true
      try {
        await settingsApi.updateSettings(form)
        originalSettings.value = { ...form }
      } catch (error) {
        console.error('保存设置失败:', error)
      } finally {
        saving.value = false
      }
    }

    const resetForm = () => {
      Object.assign(form, originalSettings.value)
    }

    // 初始加载
    loadSettings()
    loadSystemInfo()
    
    // 定期更新系统信息
    setInterval(loadSystemInfo, 30000)

    return {
      form,
      saving,
      systemInfo,
      hasChanges,
      saveSettings,
      resetForm
    }
  }
}
</script>

<style lang="scss" scoped>
.settings-view {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.settings-section {
  background: var(--card-background);
  border-radius: var(--border-radius);
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

  h2 {
    margin-top: 0;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--border-color);
  }
}

.settings-form {
  .form-group {
    margin-bottom: 20px;

    label {
      display: block;
      margin-bottom: 5px;
      font-weight: 500;
    }

    input {
      width: 100%;
      padding: 8px;
      border: 1px solid var(--border-color);
      border-radius: var(--border-radius);
      background: var(--input-background);
      color: var(--text-color);
    }

    small {
      display: block;
      margin-top: 5px;
      color: var(--text-secondary);
      font-size: 0.9em;
    }
  }
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;

  button {
    padding: 8px 16px;
    border: none;
    border-radius: var(--border-radius);
    cursor: pointer;
    transition: opacity 0.2s;

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    &.save-btn {
      background: var(--primary-color);
      color: white;
    }

    &.reset-btn {
      background: var(--warning-color);
      color: white;
    }
  }
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;

  .info-item {
    padding: 10px;
    background: var(--background-color);
    border-radius: var(--border-radius);
    display: flex;
    flex-direction: column;
    gap: 5px;

    strong {
      color: var(--text-secondary);
      font-size: 0.9em;
    }

    span {
      font-size: 1.1em;
    }
  }
}
</style> 