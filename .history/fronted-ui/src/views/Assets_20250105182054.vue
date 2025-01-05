<template>
  <div class="assets-container">
    <!-- 顶部操作栏 -->
    <div class="action-bar mac-card">
      <div class="left-actions">
        <!-- 搜索框 -->
        <div class="search-box">
          <MagnifyingGlassIcon class="search-icon" />
          <input 
            type="text" 
            v-model="searchQuery"
            placeholder="搜索资产..." 
            class="mac-search-input"
          >
        </div>
        
        <!-- 过滤器组 -->
        <div class="filter-group">
          <div class="filter-item">
            <select v-model="statusFilter" class="mac-filter-select">
              <option value="">状态</option>
              <option value="CONNECTED">已连接</option>
              <option value="PENDING">待连接</option>
              <option value="CONNECTION_ERROR">连接错误</option>
            </select>
          </div>
          <div class="filter-item">
            <select v-model="capabilityFilter" class="mac-filter-select">
              <option value="">能力</option>
              <option value="lora">Lora训练</option>
              <option value="ai">AI引擎</option>
            </select>
          </div>
        </div>
      </div>
      
      <!-- 新建按钮 -->
      <button class="mac-action-btn" @click="showCreateAsset">
        <PlusIcon class="btn-icon" />
        新建资产
      </button>
    </div>

    <!-- 资产列表 -->
    <div class="assets-grid">
      <div v-for="asset in paginatedAssets" 
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
            {{ getStatusText(asset.status) }}
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
          <div class="info-item">
            <ClockIcon class="info-icon" />
            <span>{{ formatDate(asset.updated_at) }}</span>
          </div>
        </div>

        <div class="capabilities">
          <div class="capability-tag" 
               v-if="asset.lora_training?.enabled"
               :class="{ 'is-verified': asset.lora_training?.verified }">
            <BeakerIcon class="tag-icon" />
            Lora训练
          </div>
          <div class="capability-tag" 
               v-if="asset.ai_engine?.enabled"
               :class="{ 'is-verified': asset.ai_engine?.verified }">
            <CpuChipIcon class="tag-icon" />
            AI引擎
          </div>
        </div>
        
        <div class="asset-actions">
          <button class="mac-btn small" @click.stop="verifyCapabilities(asset)">
            <CheckCircleIcon class="btn-icon" />
            验证
          </button>
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

    <!-- 分页器 -->
    <div class="pagination mac-card" v-if="totalPages > 1">
      <button 
        class="mac-btn" 
        :disabled="currentPage === 1"
        @click="currentPage--"
      >
        <ChevronLeftIcon class="btn-icon" />
      </button>
      <div class="page-numbers">
        <button 
          v-for="page in displayedPages" 
          :key="page"
          class="mac-btn page-number"
          :class="{ active: currentPage === page }"
          @click="currentPage = page"
        >
          {{ page }}
        </button>
      </div>
      <button 
        class="mac-btn" 
        :disabled="currentPage === totalPages"
        @click="currentPage++"
      >
        <ChevronRightIcon class="btn-icon" />
      </button>
    </div>

    <!-- 资产表单弹窗 -->
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
              <input 
                v-model="assetForm.name" 
                class="mac-input"
                :class="{ 'is-error': formErrors.name }"
                @input="handleFieldChange('name', $event.target.value)"
              >
              <span class="error-message" v-if="formErrors.name">{{ formErrors.name }}</span>
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
import { ref, computed, onMounted } from 'vue'
import { format } from 'date-fns'
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
  MagnifyingGlassIcon,
  ClockIcon,
  CheckCircleIcon,
  ChevronLeftIcon,
  ChevronRightIcon
} from '@heroicons/vue/24/outline'
import { assetApi } from '@/api/asset'

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
    MagnifyingGlassIcon,
    ClockIcon,
    CheckCircleIcon,
    ChevronLeftIcon,
    ChevronRightIcon
  },

  setup() {
    const assets = ref([])
    const searchQuery = ref('')
    const statusFilter = ref('')
    const capabilityFilter = ref('')
    const currentPage = ref(1)
    const pageSize = ref(12)
    
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
        params: {}
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
          params: {}
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
      let result = assets.value

      // 搜索过滤
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        result = result.filter(asset => 
          asset.name.toLowerCase().includes(query) ||
          asset.ip.includes(query)
        )
      }

      // 状态过滤
      if (statusFilter.value) {
        result = result.filter(asset => 
          asset.status === statusFilter.value
        )
      }

      // 能力过滤
      if (capabilityFilter.value) {
        result = result.filter(asset => {
          if (capabilityFilter.value === 'lora') {
            return asset.lora_training?.enabled
          }
          if (capabilityFilter.value === 'ai') {
            return asset.ai_engine?.enabled
          }
          return true
        })
      }

      return result
    })

    // 分页数据
    const totalPages = computed(() => 
      Math.ceil(filteredAssets.value.length / pageSize.value)
    )

    const paginatedAssets = computed(() => {
      const start = (currentPage.value - 1) * pageSize.value
      const end = start + pageSize.value
      return filteredAssets.value.slice(start, end)
    })

    // 显示的页码范围
    const displayedPages = computed(() => {
      const delta = 2
      const range = []
      const rangeWithDots = []
      let l

      for (let i = 1; i <= totalPages.value; i++) {
        if (
          i === 1 || 
          i === totalPages.value || 
          i >= currentPage.value - delta && 
          i <= currentPage.value + delta
        ) {
          range.push(i)
        }
      }

      range.forEach(i => {
        if (l) {
          if (i - l === 2) {
            rangeWithDots.push(l + 1)
          } else if (i - l !== 1) {
            rangeWithDots.push('...')
          }
        }
        rangeWithDots.push(i)
        l = i
      })

      return rangeWithDots
    })

    // 获取资产列表
    const fetchAssets = async () => {
      try {
        const data = await assetApi.getAssets()
        assets.value = data
      } catch (error) {
        console.error('获取资产列表失败:', error)
      }
    }

    // 提交表单
    const handleSubmit = async () => {
      if (!validateForm()) {
        return
      }

      try {
        if (isEditing.value) {
          await assetApi.updateAsset(assetForm.value.id, assetForm.value)
        } else {
          await assetApi.createAsset(assetForm.value)
        }
        
        showAssetModal.value = false
        await fetchAssets()
        resetForm()
      } catch (error) {
        alert(error.message)
      }
    }

    // 删除资产
    const confirmDelete = async (asset) => {
      if (confirm('确定要删除该资产吗？')) {
        try {
          await assetApi.deleteAsset(asset.id)
          await fetchAssets()
        } catch (error) {
          alert(error.message)
        }
      }
    }

    // 验证资产能力
    const verifyCapabilities = async (asset) => {
      try {
        const results = await assetApi.verifyCapabilities(asset.id)
        // 更新资产状态
        const index = assets.value.findIndex(a => a.id === asset.id)
        if (index !== -1) {
          assets.value[index] = {
            ...assets.value[index],
            lora_training: {
              ...assets.value[index].lora_training,
              verified: results.lora_training
            },
            ai_engine: {
              ...assets.value[index].ai_engine,
              verified: results.ai_engine
            }
          }
        }
      } catch (error) {
        alert(error.message)
      }
    }

    // 格式化日期
    const formatDate = (date) => {
      if (!date) return ''
      try {
        return format(new Date(date), 'yyyy-MM-dd HH:mm')
      } catch (error) {
        console.error('日期格式化错误:', error)
        return date
      }
    }

    // 获取状态文本
    const getStatusText = (status) => {
      const statusMap = {
        'CONNECTED': '已连接',
        'PENDING': '待连接',
        'CONNECTION_ERROR': '连接错误'
      }
      return statusMap[status] || status
    }

    // 显示编辑模态框
    const showEditModal = (asset) => {
      isEditing.value = true
      assetForm.value = { ...asset }
      showAssetModal.value = true
    }

    // 选择资产
    const selectAsset = (asset) => {
      selectedAsset.value = asset
    }

    // 表单验证规则
    const formRules = {
      name: [
        { required: true, message: '请输入资产名称' },
        { min: 2, max: 50, message: '长度在 2 到 50 个字符' }
      ],
      ip: [
        { required: true, message: '请输入IP地址' },
        { pattern: /^(\d{1,3}\.){3}\d{1,3}$/, message: 'IP地址格式不正确' }
      ],
      ssh_port: [
        { required: true, message: '请输入SSH端口' },
        { type: 'number', min: 1, max: 65535, message: '端口范围为 1-65535' }
      ],
      ssh_username: [
        { required: true, message: '请输入SSH用户名' }
      ]
    }

    // 表单错误信息
    const formErrors = ref({})

    // 验证单个字段
    const validateField = (field, value) => {
      const rules = formRules[field]
      if (!rules) return true

      for (const rule of rules) {
        if (rule.required && !value) {
          formErrors.value[field] = rule.message
          return false
        }
        if (rule.min && value.length < rule.min) {
          formErrors.value[field] = rule.message
          return false
        }
        if (rule.max && value.length > rule.max) {
          formErrors.value[field] = rule.message
          return false
        }
        if (rule.pattern && !rule.pattern.test(value)) {
          formErrors.value[field] = rule.message
          return false
        }
        if (rule.type === 'number') {
          const num = Number(value)
          if (isNaN(num) || num < rule.min || num > rule.max) {
            formErrors.value[field] = rule.message
            return false
          }
        }
      }
      delete formErrors.value[field]
      return true
    }

    // 验证整个表单
    const validateForm = () => {
      let isValid = true
      formErrors.value = {}

      Object.keys(formRules).forEach(field => {
        if (!validateField(field, assetForm.value[field])) {
          isValid = false
        }
      })

      // 验证能力配置
      if (assetForm.value.lora_training.enabled) {
        if (!assetForm.value.lora_training.url) {
          formErrors.value['lora_url'] = '请输入Lora训练服务URL'
          isValid = false
        }
        if (!assetForm.value.lora_training.port) {
          formErrors.value['lora_port'] = '请输入Lora训练服务端口'
          isValid = false
        }
      }

      if (assetForm.value.ai_engine.enabled) {
        if (!assetForm.value.ai_engine.url) {
          formErrors.value['ai_url'] = '请输入AI引擎服务URL'
          isValid = false
        }
        if (!assetForm.value.ai_engine.port) {
          formErrors.value['ai_port'] = '请输入AI引擎服务端口'
          isValid = false
        }
      }

      return isValid
    }

    // 字段值改变时验证
    const handleFieldChange = (field, value) => {
      assetForm.value[field] = value
      validateField(field, value)
    }

    // 显示新建资产弹窗
    const showCreateAsset = () => {
      isEditing.value = false
      resetForm()
      showAssetModal.value = true
    }

    // 在组件挂载时获取资产列表
    onMounted(() => {
      fetchAssets()
    })

    return {
      assets,
      searchQuery,
      selectedAsset,
      showAssetModal,
      isEditing,
      assetForm,
      statusFilter,
      capabilityFilter,
      currentPage,
      totalPages,
      paginatedAssets,
      displayedPages,
      verifyCapabilities,
      formatDate,
      getStatusText,
      showEditModal,
      selectAsset,
      handleSubmit,
      confirmDelete,
      showCreateAsset,
      formErrors,
      handleFieldChange
    }
  }
}
</script>

<style scoped>
.assets-container {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 100%;
  background: transparent;
}

.action-bar {
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.left-actions {
  display: flex;
  gap: 20px;
  align-items: center;
}

.search-box {
  position: relative;
  min-width: 240px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  color: #8E8E93;
}

.mac-search-input {
  width: 100%;
  height: 32px;
  padding: 0 12px 0 36px;
  border-radius: 8px;
  border: none;
  background: rgba(142, 142, 147, 0.12);
  color: #1C1C1E;
  font-size: 14px;
  transition: all 0.3s ease;
}

.mac-search-input:focus {
  background: rgba(142, 142, 147, 0.18);
  outline: none;
}

.mac-search-input::placeholder {
  color: #8E8E93;
}

.filter-group {
  display: flex;
  gap: 12px;
}

.filter-item {
  position: relative;
}

.mac-filter-select {
  height: 32px;
  padding: 0 28px 0 12px;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  background: transparent;
  color: #1C1C1E;
  font-size: 14px;
  cursor: pointer;
  appearance: none;
  transition: all 0.2s ease;
}

.mac-filter-select:hover {
  background: rgba(142, 142, 147, 0.08);
}

.mac-filter-select:focus {
  outline: none;
  border-color: #007AFF;
  box-shadow: 0 0 0 2px rgba(0, 122, 255, 0.1);
}

.mac-action-btn {
  height: 32px;
  padding: 0 16px;
  border-radius: 8px;
  border: none;
  background: #007AFF;
  color: white;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mac-action-btn:hover {
  background: #0066D6;
  transform: translateY(-1px);
}

.mac-action-btn:active {
  background: #0055B3;
  transform: translateY(0);
}

.btn-icon {
  width: 16px;
  height: 16px;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .action-bar {
    flex-direction: column;
    gap: 12px;
  }
  
  .left-actions {
    width: 100%;
    flex-direction: column;
  }
  
  .search-box {
    width: 100%;
  }
  
  .filter-group {
    width: 100%;
  }
  
  .filter-item {
    flex: 1;
  }
  
  .mac-filter-select {
    width: 100%;
  }
  
  .mac-action-btn {
    width: 100%;
    justify-content: center;
  }
}

.assets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  flex: 1;
  overflow-y: auto;
}

.asset-card {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 200px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(8px);
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

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 12px;
  gap: 8px;
}

.page-numbers {
  display: flex;
  gap: 4px;
}

.page-number {
  min-width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.page-number.active {
  background: var(--primary-color);
  color: white;
}

.capability-tag.is-verified {
  background: var(--success-color);
}

/* 添加状态样式 */
.asset-status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.asset-status.connected {
  background: var(--success-color);
  color: white;
}

.asset-status.pending {
  background: #FEF3C7;
  color: #92400E;
}

.asset-status.connection_error {
  background: var(--danger-color);
  color: white;
}

.search-box {
  position: relative;
  min-width: 300px;
}

.search-input {
  width: 100%;
  padding-left: 36px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  color: var(--text-secondary);
  pointer-events: none;
}

.filter-box {
  display: flex;
  gap: 12px;
}

.mac-select {
  min-width: 120px;
}

.left-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* 添加一些动画效果 */
.mac-btn {
  transition: all 0.2s ease;
}

.mac-btn:active {
  transform: translateY(1px);
}

.mac-card {
  transition: all 0.3s ease;
}

.asset-card {
  cursor: pointer;
}

.asset-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0,0,0,0.1);
}

/* 添加加载状态样式 */
.loading {
  opacity: 0.7;
  pointer-events: none;
}

/* 优化表单样式 */
.form-section {
  background: white;
  border: 1px solid var(--border-color, #E5E7EB);
}

.capability-form {
  background: var(--background-primary);
}

/* 添加响应式布局 */
@media (max-width: 768px) {
  .left-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-box {
    flex-wrap: wrap;
  }

  .assets-grid {
    grid-template-columns: 1fr;
  }
}

.is-error {
  border-color: var(--danger-color);
}

.error-message {
  color: var(--danger-color);
  font-size: 12px;
  margin-top: var(--spacing-1);
  display: block;
}

.form-item {
  margin-bottom: var(--spacing-4);
}
</style> 