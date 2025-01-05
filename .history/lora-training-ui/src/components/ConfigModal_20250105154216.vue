<template>
  <div>
    <div class="modal-overlay" @click="$emit('close')"></div>
    <div class="modal config-modal">
      <div class="modal-header">
        <h2>系统配置</h2>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>
      <div class="modal-body">
        <form class="config-form" @submit.prevent="saveConfig">
          <div class="form-group">
            <label>源文件目录</label>
            <input 
              type="text" 
              v-model="configForm.source_dir"
              @input="onConfigChange"
              placeholder="训练数据源文件目录"
            >
          </div>
          <div class="form-group">
            <label>Lora输出路径</label>
            <input 
              type="text" 
              v-model="configForm.lora_output_path"
              @input="onConfigChange"
              placeholder="训练完成的Lora模型输出路径"
            >
          </div>
          <div class="form-group">
            <label>定时检查间隔（分钟）</label>
            <input 
              type="number" 
              v-model="configForm.scheduling_minute"
              @input="onConfigChange"
              min="1"
              step="1"
            >
          </div>
          <div class="form-group">
            <label>API地址</label>
            <input 
              type="url" 
              v-model="configForm.url"
              @input="onConfigChange"
              placeholder="http://127.0.0.1:28000"
            >
          </div>
          <div class="form-group">
            <label>云盘标记文件目录</label>
            <input 
              type="text" 
              v-model="configForm.mark_pan_dir"
              @input="onConfigChange"
              placeholder="/loraFile/mark"
            >
          </div>
          <div class="form-group">
            <label>云盘Lora上传目录</label>
            <input 
              type="text" 
              v-model="configForm.lora_pan_upload_dir"
              @input="onConfigChange"
              placeholder="/loraFile/lora"
            >
          </div>
          <div class="form-actions">
            <button 
              type="submit" 
              class="save-btn"
              :disabled="!configChanged"
            >
              保存更改
            </button>
          </div>
        </form>
        <div class="config-error" v-if="configError">
          {{ configError }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getCurrentInstance, ref } from 'vue'

export default {
  name: 'ConfigModal',
  setup() {
    const { proxy } = getCurrentInstance()
    const configForm = ref({
      source_dir: '',
      lora_output_path: '',
      scheduling_minute: 2,
      url: 'http://127.0.0.1:28000',
      mark_pan_dir: '/loraFile/mark',
      lora_pan_upload_dir: '/loraFile/lora'
    })
    const configChanged = ref(false)
    const configError = ref('')

    const loadConfig = async () => {
      try {
        const response = await proxy.$http.get('/api/config')
        if (response.data.success) {
          const config = response.data.data
          configForm.value = {
            source_dir: config.source_dir || '',
            lora_output_path: config.lora_output_path || '',
            scheduling_minute: config.scheduling_minute || 2,
            url: config.url || 'http://127.0.0.1:28000',
            mark_pan_dir: config.mark_pan_dir || '/loraFile/mark',
            lora_pan_upload_dir: config.lora_pan_upload_dir || '/loraFile/lora'
          }
          configChanged.value = false
          configError.value = ''
        }
      } catch (error) {
        console.error('加载配置失败:', error)
        configError.value = '加载配置失败'
      }
    }

    const saveConfig = async () => {
      try {
        const config = {
          source_dir: configForm.value.source_dir,
          lora_output_path: configForm.value.lora_output_path,
          scheduling_minute: parseInt(configForm.value.scheduling_minute),
          url: configForm.value.url,
          mark_pan_dir: configForm.value.mark_pan_dir,
          lora_pan_upload_dir: configForm.value.lora_pan_upload_dir
        }
        
        const response = await proxy.$http.post('/api/config', config)
        if (response.data.success) {
          configError.value = ''
          configChanged.value = false
          proxy.$emit('close')
          alert('配置已保存')
        }
      } catch (error) {
        console.error('保存配置失败:', error)
        configError.value = error.message || '保存配置失败'
      }
    }

    const onConfigChange = () => {
      configChanged.value = true
    }

    return {
      configForm,
      configChanged,
      configError,
      loadConfig,
      saveConfig,
      onConfigChange
    }
  },
  mounted() {
    this.loadConfig()
  }
}
</script> 