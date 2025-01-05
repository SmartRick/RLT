<template>
  <div class="assets-container">
    <!-- 顶部操作栏 -->
    <div class="action-bar mac-card">
      <div class="left-actions">
        <div class="search-box">
          <MagnifyingGlassIcon class="search-icon" />
          <input 
            type="text" 
            v-model="searchQuery"
            placeholder="搜索资产..." 
            class="mac-input search-input"
          >
        </div>
        <div class="filter-box">
          <select v-model="statusFilter" class="mac-select">
            <option value="">全部状态</option>
            <option value="CONNECTED">已连接</option>
            <option value="PENDING">待连接</option>
            <option value="CONNECTION_ERROR">连接错误</option>
          </select>
        </div>
      </div>
      <button class="mac-btn primary" @click="showCreateAsset">
        <PlusIcon class="btn-icon" />
        新建资产
      </button>
    </div>

    <!-- 资产列表 -->
    <div class="assets-grid">
      <div v-for="asset in filteredAssets" 
           :key="asset.id" 
           class="asset-card mac-card"
           :class="{ 'is-selected': selectedAsset?.id === asset.id }">
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
        </div>

        <div class="capabilities">
          <div v-if="asset.lora_training?.enabled" 
               class="capability-tag"
               :class="{ 'is-verified': asset.lora_training?.verified }">
            <BeakerIcon class="tag-icon" />
            Lora训练
          </div>
          <div v-if="asset.ai_engine?.enabled" 
               class="capability-tag"
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
      return assets.value.filter(asset => {
        const matchesSearch = asset.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                            asset.ip.includes(searchQuery.value)
        
        const matchesStatus = !statusFilter.value || 
                            asset.status.toLowerCase() === statusFilter.value.toLowerCase()
        
        return matchesSearch && matchesStatus
      })
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
      handleFieldChange,
      filteredAssets
    }
  }
}
</script>

<style scoped>
.assets-container {
  padding: var(--spacing-4);
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.action-bar {
  padding: var(--spacing-4);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--background-secondary);
}

.left-actions {
  display: flex;
  gap: var(--spacing-4);
  align-items: center;
}

.assets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--spacing-4);
  overflow-y: auto;
  padding: var(--spacing-2);
}

.asset-card {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
  padding: var(--spacing-4);
  background: var(--background-secondary);
  transition: all var(--transition-speed);
}

.asset-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.asset-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.asset-name {
  font-weight: 500;
  font-size: 16px;
}

.asset-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.info-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  color: var(--text-secondary);
}

.capabilities {
  display: flex;
  gap: var(--spacing-2);
  flex-wrap: wrap;
}

.capability-tag {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-1);
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  background: var(--primary-color);
  color: white;
}

.capability-tag.is-verified {
  background: var(--success-color);
}

.asset-actions {
  display: flex;
  gap: var(--spacing-2);
  margin-top: auto;
}

.asset-status {
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
}

.asset-status.connected {
  background: var(--success-color);
  color: white;
}

.asset-status.pending {
  background: var(--warning-color);
  color: white;
}

.asset-status.connection_error {
  background: var(--danger-color);
  color: white;
}

/* 图标样式 */
.asset-icon,
.info-icon,
.tag-icon,
.btn-icon {
  width: 20px;
  height: 20px;
}

.info-icon {
  color: var(--text-tertiary);
}

/* 响应式布局 */
@media (max-width: 768px) {
  .left-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .search-box {
    width: 100%;
  }

  .assets-grid {
    grid-template-columns: 1fr;
  }
}
</style> 