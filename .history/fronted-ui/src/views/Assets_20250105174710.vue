<template>
  <div class="assets-container">
    <!-- 顶部操作栏 -->
    <div class="action-bar mac-card">
      <div class="search-box">
        <MagnifyingGlassIcon class="search-icon" />
        <input 
          type="text" 
          v-model="searchQuery"
          placeholder="搜索资产..." 
          class="mac-input"
        >
      </div>
      <button class="mac-btn primary" @click="showCreateModal = true">
        <PlusIcon class="btn-icon" />
        新建资产
      </button>
    </div>

    <!-- 资产列表 -->
    <div class="assets-grid">
      <div v-for="asset in filteredAssets" 
           :key="asset.id" 
           class="asset-card mac-card"
           :class="{ 'is-selected': selectedAsset?.id === asset.id }"
           @click="selectAsset(asset)">
        <div class="asset-header">
          <div class="asset-title">
            <ServerIcon class="asset-icon" />
            <span class="asset-name">{{ asset.name }}</span>
          </div>
          <div class="asset-status" :class="asset.status.toLowerCase()">
            {{ asset.status }}
          </div>
        </div>
        
        <div class="asset-info">
          <div class="info-item">
            <ComputerDesktopIcon class="info-icon" />
            <span>{{ asset.ip }}:{{ asset.ssh_port }}</span>
          </div>
          <div class="info-item">
            <UserIcon class="info-icon" />
            <span>{{ asset.ssh_username }}</span>
          </div>
        </div>

        <div class="capabilities">
          <div class="capability-tag" v-if="asset.lora_training">
            <BeakerIcon class="tag-icon" />
            Lora训练
          </div>
          <div class="capability-tag" v-if="asset.ai_engine">
            <CpuChipIcon class="tag-icon" />
            AI引擎
          </div>
        </div>
        
        <div class="asset-actions">
          <button class="mac-btn small" @click.stop="showEditModal(asset)">
            <PencilIcon class="btn-icon" />
            编辑
          </button>
          <button class="mac-btn small danger" @click.stop="confirmDelete(asset)">
            <TrashIcon class="btn-icon" />
            删除
          </button>
        </div>
      </div>
    </div>

    <!-- 新建/编辑资产弹窗 -->
    <BaseModal 
      v-model="showAssetModal"
      :title="isEditing ? '编辑资产' : '新建资产'"
    >
      <template #body>
        <form @submit.prevent="handleSubmit" class="asset-form">
          <div class="form-section">
            <h3 class="section-title">基本信息</h3>
            <div class="form-item">
              <label>资产名称</label>
              <input v-model="assetForm.name" class="mac-input" required>
            </div>
            <div class="form-row">
              <div class="form-item">
                <label>IP地址</label>
                <input v-model="assetForm.ip" class="mac-input" required>
              </div>
              <div class="form-item">
                <label>SSH端口</label>
                <input v-model="assetForm.ssh_port" type="number" class="mac-input" required>
              </div>
            </div>
            <div class="form-row">
              <div class="form-item">
                <label>SSH用户名</label>
                <input v-model="assetForm.ssh_username" class="mac-input" required>
              </div>
              <div class="form-item">
                <label>SSH密钥路径</label>
                <input v-model="assetForm.ssh_key_path" class="mac-input">
              </div>
            </div>
          </div>

          <div class="form-section">
            <div class="section-header">
              <h3 class="section-title">Lora训练能力</h3>
              <switch-button v-model="assetForm.lora_training.enabled" />
            </div>
            <div v-show="assetForm.lora_training.enabled" class="capability-form">
              <div class="form-row">
                <div class="form-item">
                  <label>服务URL</label>
                  <input v-model="assetForm.lora_training.url" class="mac-input">
                </div>
                <div class="form-item">
                  <label>服务端口</label>
                  <input v-model="assetForm.lora_training.port" type="number" class="mac-input">
                </div>
              </div>
              <div class="form-item">
                <label>配置文件路径</label>
                <input v-model="assetForm.lora_training.config_path" class="mac-input">
              </div>
              <div class="form-item">
                <label>训练参数配置</label>
                <textarea 
                  v-model="assetForm.lora_training.params" 
                  class="mac-textarea"
                  placeholder="请输入JSON格式的训练参数配置"
                ></textarea>
              </div>
            </div>
          </div>

          <div class="form-section">
            <div class="section-header">
              <h3 class="section-title">AI引擎能力</h3>
              <switch-button v-model="assetForm.ai_engine.enabled" />
            </div>
            <div v-show="assetForm.ai_engine.enabled" class="capability-form">
              <div class="form-row">
                <div class="form-item">
                  <label>服务URL</label>
                  <input v-model="assetForm.ai_engine.url" class="mac-input">
                </div>
                <div class="form-item">
                  <label>服务端口</label>
                  <input v-model="assetForm.ai_engine.port" type="number" class="mac-input">
                </div>
              </div>
            </div>
          </div>
        </form>
      </template>
      <template #footer>
        <button class="mac-btn" @click="showAssetModal = false">取消</button>
        <button class="mac-btn primary" @click="handleSubmit">确认</button>
      </template>
    </BaseModal>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import BaseModal from '@/components/common/Modal.vue'
import SwitchButton from '@/components/common/SwitchButton.vue'
import {
  PlusIcon,
  ServerIcon,
  ComputerDesktopIcon,
  UserIcon,
  BeakerIcon,
  CpuChipIcon,
  PencilIcon,
  TrashIcon,
  MagnifyingGlassIcon
} from '@heroicons/vue/24/outline'

export default {
  name: 'AssetManager',
  components: {
    BaseModal,
    SwitchButton,
    PlusIcon,
    ServerIcon,
    ComputerDesktopIcon,
    UserIcon,
    BeakerIcon,
    CpuChipIcon,
    PencilIcon,
    TrashIcon,
    MagnifyingGlassIcon
  },

  setup() {
    const assets = ref([])
    const searchQuery = ref('')
    const selectedAsset = ref(null)
    const showAssetModal = ref(false)
    const isEditing = ref(false)

    const assetForm = ref({
      name: '',
      ip: '',
      ssh_port: 22,
      ssh_username: '',
      ssh_key_path: '',
      lora_training: {
        enabled: false,
        url: '',
        port: null,
        config_path: '',
        params: ''
      },
      ai_engine: {
        enabled: false,
        url: '',
        port: null
      }
    })

    const resetForm = () => {
      assetForm.value = {
        name: '',
        ip: '',
        ssh_port: 22,
        ssh_username: '',
        ssh_key_path: '',
        lora_training: {
          enabled: false,
          url: '',
          port: null,
          config_path: '',
          params: ''
        },
        ai_engine: {
          enabled: false,
          url: '',
          port: null
        }
      }
    }

    // 过滤资产列表
    const filteredAssets = computed(() => {
      if (!searchQuery.value) return assets.value
      const query = searchQuery.value.toLowerCase()
      return assets.value.filter(asset => 
        asset.name.toLowerCase().includes(query) ||
        asset.ip.includes(query)
      )
    })

    // 获取资产列表
    const fetchAssets = async () => {
      try {
        const response = await fetch('/api/v1/assets')
        assets.value = await response.json()
      } catch (error) {
        console.error('获取资产列表失败:', error)
      }
    }

    // 显示编辑模态框
    const showEditModal = (asset) => {
      isEditing.value = true
      assetForm.value = { ...asset }
      showAssetModal.value = true
    }

    // 提交表单
    const handleSubmit = async () => {
      try {
        const url = isEditing.value 
          ? `/api/v1/assets/${assetForm.value.id}`
          : '/api/v1/assets'
        
        const response = await fetch(url, {
          method: isEditing.value ? 'PUT' : 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(assetForm.value)
        })
        
        if (response.ok) {
          showAssetModal.value = false
          await fetchAssets()
          resetForm()
          isEditing.value = false
        }
      } catch (error) {
        console.error('保存资产失败:', error)
      }
    }

    // 删除资产
    const confirmDelete = async (asset) => {
      if (confirm(`确定要删除资产 "${asset.name}" 吗？`)) {
        try {
          const response = await fetch(`/api/v1/assets/${asset.id}`, {
            method: 'DELETE'
          })
          if (response.ok) {
            await fetchAssets()
          }
        } catch (error) {
          console.error('删除资产失败:', error)
        }
      }
    }

    return {
      assets,
      searchQuery,
      selectedAsset,
      showAssetModal,
      isEditing,
      assetForm,
      filteredAssets,
      showEditModal,
      handleSubmit,
      confirmDelete
    }
  }
}
</script>

<style scoped>
.assets-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
}

.mac-input {
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 14px;
  transition: all 0.3s;
}

.mac-input:focus {
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52,152,219,0.2);
}

.assets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  padding: 10px;
  overflow-y: auto;
}

.asset-card {
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.asset-card.is-selected {
  border: 2px solid #3498db;
}

.asset-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.asset-name {
  font-weight: 600;
  font-size: 16px;
}

.asset-type {
  background: #e1f0ff;
  color: #3498db;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.asset-info {
  display: flex;
  gap: 15px;
  color: #666;
  font-size: 13px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.asset-actions {
  display: flex;
  gap: 10px;
  margin-top: auto;
}

.upload-area {
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.upload-area:hover {
  border-color: #3498db;
  background: #f8f9fa;
}

.upload-hint {
  color: #606266;
}

.upload-list {
  margin-top: 20px;
}

.upload-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-bottom: 1px solid #eee;
}

.progress-bar {
  flex: 1;
  height: 4px;
  background: #eee;
  border-radius: 2px;
  overflow: hidden;
}

.progress {
  height: 100%;
  background: #3498db;
  transition: width 0.3s ease;
}

/* 添加主按钮样式 */
.mac-btn.primary {
  background: linear-gradient(to bottom, #3498db 0%, #2980b9 100%);
  color: white;
  border: none;
}

.mac-btn.primary:hover {
  background: linear-gradient(to bottom, #2980b9 0%, #2472a4 100%);
}

.mac-btn.danger {
  background: linear-gradient(to bottom, #e74c3c 0%, #c0392b 100%);
  color: white;
  border: none;
}

.mac-btn.danger:hover {
  background: linear-gradient(to bottom, #c0392b 0%, #a93224 100%);
}

.mac-btn.small {
  padding: 4px 8px;
  font-size: 12px;
}

/* 添加表单样式 */
.form-item {
  margin-bottom: 15px;
}

.form-item label {
  display: block;
  margin-bottom: 5px;
  color: #606266;
}

.mac-select,
.mac-textarea {
  width: 100%;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 14px;
  transition: all 0.3s;
}

.mac-textarea {
  min-height: 100px;
  resize: vertical;
}

.mac-select:focus,
.mac-textarea:focus {
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52,152,219,0.2);
}

.form-section {
  margin-bottom: 24px;
  padding: 16px;
  background: var(--background-primary);
  border-radius: var(--border-radius);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.capability-form {
  padding: 16px;
  background: white;
  border-radius: var(--border-radius);
  margin-top: 12px;
}

.capability-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: var(--primary-color);
  color: white;
  border-radius: 4px;
  font-size: 12px;
}

.tag-icon {
  width: 14px;
  height: 14px;
}

.asset-status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.asset-status.pending {
  background: #FEF3C7;
  color: #92400E;
}

.asset-status.running {
  background: #D1FAE5;
  color: #065F46;
}

.asset-status.error {
  background: #FEE2E2;
  color: #991B1B;
}

.btn-icon {
  width: 16px;
  height: 16px;
  margin-right: 4px;
}

.info-icon {
  width: 16px;
  height: 16px;
  color: var(--text-secondary);
}
</style> 