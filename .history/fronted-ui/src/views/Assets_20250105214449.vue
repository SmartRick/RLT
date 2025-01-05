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
        <!-- 卡片头部 -->
        <div class="asset-card-header">
          <div class="asset-title">
            <ServerIcon class="asset-icon" />
            <span class="asset-name text-ellipsis">{{ asset.name }}</span>
          </div>
          <div class="asset-status-badge" :class="asset.status.toLowerCase()">
            {{ getStatusText(asset.status) }}
          </div>
        </div>

        <!-- 卡片内容 -->
        <div class="asset-card-content">
          <div class="info-grid">
            <div class="info-item">
              <ComputerDesktopIcon class="info-icon" />
              <span class="info-text text-ellipsis">{{ asset.ip }}:{{ asset.ssh_port }}</span>
            </div>
            <div class="info-item">
              <UserIcon class="info-icon" />
              <span class="info-text text-ellipsis">{{ asset.ssh_username }}</span>
            </div>
            <div class="info-item">
              <ClockIcon class="info-icon" />
              <span class="info-text text-ellipsis">{{ formatDate(asset.updated_at) }}</span>
            </div>
          </div>

          <!-- 能力标签组 -->
          <div class="capability-tags">
            <div class="capability-tag" 
                 v-if="asset.lora_training?.enabled"
                 :class="{ 'is-verified': asset.lora_training?.verified }">
              <BeakerIcon class="tag-icon" />
              <span>Lora训练</span>
            </div>
            <div class="capability-tag" 
                 v-if="asset.ai_engine?.enabled"
                 :class="{ 'is-verified': asset.ai_engine?.verified }">
              <CpuChipIcon class="tag-icon" />
              <span>AI引擎</span>
            </div>
          </div>
        </div>

        <!-- 卡片操作栏 -->
        <div class="asset-card-actions">
          <button class="mac-btn small terminal-btn" @click.stop="openTerminal(asset)">
            <TerminalIcon class="btn-icon" />
            <span>终端</span>
          </button>
          <button class="mac-btn small verify-btn" @click.stop="verifyCapabilities(asset)">
            <CheckCircleIcon class="btn-icon" />
            <span>验证</span>
          </button>
          <button class="mac-btn small edit-btn" @click.stop="showEditModal(asset)">
            <PencilIcon class="btn-icon" />
            <span>编辑</span>
          </button>
          <button class="mac-btn small delete-btn" @click.stop="confirmDelete(asset)">
            <TrashIcon class="btn-icon" />
            <span>删除</span>
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
                @blur="validateField('name', assetForm.name)"
              >
              <span class="error-message" v-if="formErrors.name">{{ formErrors.name }}</span>
            </div>
            <div class="form-row">
              <div class="form-item">
                <label>IP地址</label>
                <input 
                  v-model="assetForm.ip" 
                  class="mac-input"
                  :class="{ 'is-error': formErrors.ip }"
                  @blur="validateField('ip', assetForm.ip)"
                >
                <span class="error-message" v-if="formErrors.ip">{{ formErrors.ip }}</span>
              </div>
              <div class="form-item">
                <label>SSH端口</label>
                <input 
                  v-model="assetForm.ssh_port" 
                  type="number" 
                  class="mac-input"
                  :class="{ 'is-error': formErrors.ssh_port }"
                  @blur="validateField('ssh_port', assetForm.ssh_port)"
                >
                <span class="error-message" v-if="formErrors.ssh_port">{{ formErrors.ssh_port }}</span>
              </div>
            </div>
            <div class="form-row">
              <div class="form-item">
                <label>SSH用户名</label>
                <input 
                  v-model="assetForm.ssh_username" 
                  class="mac-input"
                  :class="{ 'is-error': formErrors.ssh_username }"
                  @blur="validateField('ssh_username', assetForm.ssh_username)"
                >
                <span class="error-message" v-if="formErrors.ssh_username">{{ formErrors.ssh_username }}</span>
              </div>
              <div class="form-item">
                <label>认证方式</label>
                <select 
                  v-model="assetForm.ssh_auth_type" 
                  class="mac-input"
                >
                  <option value="KEY">SSH密钥</option>
                  <option value="PASSWORD">密码</option>
                </select>
              </div>
            </div>
            
            <!-- 根据认证方式显示不同的输入框 -->
            <div class="form-item ssh-auth-input">
              <template v-if="assetForm.ssh_auth_type === 'PASSWORD'">
                <label>SSH密码</label>
                <div class="input-with-button">
                  <input 
                    v-model="assetForm.ssh_password"
                    type="password"
                    class="mac-input"
                    :class="{ 'is-error': formErrors.ssh_password }"
                    @blur="validateField('ssh_password', assetForm.ssh_password)"
                  >
                  <button 
                    class="mac-btn verify-ssh-btn" 
                    :disabled="isVerifyingSsh"
                    @click="verifySshConnection"
                  >
                    <CheckCircleIcon class="btn-icon" v-if="!isVerifyingSsh" />
                    <span class="loading-spinner" v-else></span>
                    {{ isVerifyingSsh ? '验证中...' : '验证连接' }}
                  </button>
                </div>
                <span class="error-message" v-if="formErrors.ssh_password">{{ formErrors.ssh_password }}</span>
              </template>
              
              <template v-else>
                <label>SSH密钥路径</label>
                <div class="input-with-button">
                  <input 
                    v-model="assetForm.ssh_key_path"
                    class="mac-input"
                    :class="{ 'is-error': formErrors.ssh_key_path }"
                    @blur="validateField('ssh_key_path', assetForm.ssh_key_path)"
                  >
                  <button 
                    class="mac-btn verify-ssh-btn" 
                    :disabled="isVerifyingSsh"
                    @click="verifySshConnection"
                  >
                    <CheckCircleIcon class="btn-icon" v-if="!isVerifyingSsh" />
                    <span class="loading-spinner" v-else></span>
                    {{ isVerifyingSsh ? '验证中...' : '验证连接' }}
                  </button>
                </div>
                <span class="error-message" v-if="formErrors.ssh_key_path">{{ formErrors.ssh_key_path }}</span>
              </template>
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
                  <input 
                    v-model="assetForm.lora_training.url" 
                    class="mac-input"
                    :class="{ 'is-error': formErrors.lora_url }"
                    @blur="validateCapabilityField('lora_training', 'url')"
                  >
                  <span class="error-message" v-if="formErrors.lora_url">{{ formErrors.lora_url }}</span>
                </div>
                <div class="form-item">
                  <label>服务端口</label>
                  <input 
                    v-model="assetForm.lora_training.port" 
                    type="number" 
                    class="mac-input"
                    :class="{ 'is-error': formErrors.lora_port }"
                    @blur="validateCapabilityField('lora_training', 'port')"
                  >
                  <span class="error-message" v-if="formErrors.lora_port">{{ formErrors.lora_port }}</span>
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
                  :class="{ 'is-error': formErrors.lora_params }"
                  @blur="validateCapabilityField('lora_training', 'params')"
                ></textarea>
                <span class="error-message" v-if="formErrors.lora_params">{{ formErrors.lora_params }}</span>
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
                  <input 
                    v-model="assetForm.ai_engine.url" 
                    class="mac-input"
                    :class="{ 'is-error': formErrors.ai_url }"
                    @blur="validateCapabilityField('ai_engine', 'url')"
                  >
                  <span class="error-message" v-if="formErrors.ai_url">{{ formErrors.ai_url }}</span>
                </div>
                <div class="form-item">
                  <label>服务端口</label>
                  <input 
                    v-model="assetForm.ai_engine.port" 
                    type="number" 
                    class="mac-input"
                    :class="{ 'is-error': formErrors.ai_port }"
                    @blur="validateCapabilityField('ai_engine', 'port')"
                  >
                  <span class="error-message" v-if="formErrors.ai_port">{{ formErrors.ai_port }}</span>
                </div>
              </div>
            </div>
          </div>
        </form>
      </template>
      <template #footer>
        <button class="mac-btn" @click="showAssetModal = false">取消</button>
        <button 
          type="submit" 
          class="mac-btn primary" 
          :disabled="isSubmitting"
          @click="handleSubmit"
        >
          {{ isSubmitting ? '提交中...' : '确认' }}
        </button>
      </template>
    </BaseModal>

    <!-- 添加终端弹窗组件 -->
    <WebTerminal
      v-if="showTerminal"
      v-model="showTerminal"
      :asset="selectedTerminalAsset"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, defineComponent } from 'vue'
import { format } from 'date-fns'
import BaseModal from '@/components/common/Modal.vue'
import SwitchButton from '@/components/common/SwitchButton.vue'
import message from '@/utils/message'
import { assetApi } from '@/api/asset'
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
  ChevronRightIcon,
  TerminalIcon
} from '@heroicons/vue/24/outline'
import WebTerminal from '@/components/terminal/WebTerminal.vue'

defineComponent({
  name: 'AssetsManager'
})

// 状态定义
const assets = ref([])
const searchQuery = ref('')
const statusFilter = ref('')
const capabilityFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(12)
const selectedAsset = ref(null)
const showAssetModal = ref(false)
const isEditing = ref(false)
const formErrors = ref({})
const showTerminal = ref(false)
const selectedTerminalAsset = ref(null)

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
  },
  ssh_auth_type: 'KEY',
  ssh_password: ''
})

const resetForm = () => {
  assetForm.value = {
    name: '',
    ip: '',
    ssh_port: 22,
    ssh_username: '',
    ssh_auth_type: 'KEY',
    ssh_password: '',
    ssh_key_path: '',
    lora_training: {
      enabled: false,
      url: '',
      port: null,
      config_path: '',
      params: JSON.stringify({}, null, 2)
    },
    ai_engine: {
      enabled: false,
      url: '',
      port: null
    }
  }
  formErrors.value = {}
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

// 添加提交状态
const isSubmitting = ref(false)

// 修改提交处理函数
const handleSubmit = async () => {
  if (!validateForm()) {
    return
  }

  try {
    isSubmitting.value = true
    
    // 处理表单数据
    const formData = {
      ...assetForm.value,
      // 根据认证类型处理认证信息
      ssh_password: assetForm.value.ssh_auth_type === 'PASSWORD' ? assetForm.value.ssh_password : undefined,
      ssh_key_path: assetForm.value.ssh_auth_type === 'KEY' ? assetForm.value.ssh_key_path : undefined,
      
      // 处理能力配置
      lora_training: assetForm.value.lora_training.enabled 
        ? {
            ...assetForm.value.lora_training,
            params: typeof assetForm.value.lora_training.params === 'string' 
              ? assetForm.value.lora_training.params 
              : JSON.stringify(assetForm.value.lora_training.params)
          }
        : { enabled: false, url: '', port: null, config_path: '', params: '{}' },
      ai_engine: assetForm.value.ai_engine.enabled
        ? assetForm.value.ai_engine
        : { enabled: false, url: '', port: null }
    }

    if (isEditing.value) {
      await assetApi.updateAsset(formData.id, formData)
      message.success('资产更新成功')
    } else {
      await assetApi.createAsset(formData)
      message.success('资产创建成功')
    }
    
    showAssetModal.value = false
    await fetchAssets()
    resetForm()
  } catch (error) {
    // 处理验证错误
    if (error.response?.data?.detail) {
      const errors = error.response.data.detail
      errors.forEach(err => {
        const field = err.loc[err.loc.length - 1]
        const capability = err.loc[err.loc.length - 2]
        if (capability === 'lora_training' || capability === 'ai_engine') {
          formErrors.value[`${capability.split('_')[0]}_${field}`] = err.msg
        } else {
          formErrors.value[field] = err.msg
        }
      })
    } else {
      message.error(error.message || '操作失败')
    }
  } finally {
    isSubmitting.value = false
  }
}

// 删除资产
const confirmDelete = async (asset) => {
  if (confirm('确定要删除该资产吗？')) {
    try {
      await assetApi.deleteAsset(asset.id)
      message.success('资产已删除')
      await fetchAssets()
    } catch (error) {
      message.error(error.message || '删除失败')
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
      message.success('验证完成')
    }
  } catch (error) {
    message.error(error.message || '验证失败')
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
  // 深拷贝资产数据并确保认证相关字段存在
  const assetData = {
    ...JSON.parse(JSON.stringify(asset)),
    ssh_auth_type: asset.ssh_auth_type || (asset.ssh_password ? 'PASSWORD' : 'KEY'),
    ssh_password: asset.ssh_password || '',
    ssh_key_path: asset.ssh_key_path || ''
  }
  assetForm.value = assetData
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
  ],
  ssh_password: [
    { required: true, message: '请输入SSH密码', when: (form) => form.ssh_auth_type === 'PASSWORD' }
  ],
  ssh_key_path: [
    { required: true, message: '请输入SSH密钥路径', when: (form) => form.ssh_auth_type === 'KEY' }
  ]
}

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

// 验证并格式化JSON
const validateJson = (jsonString) => {
  try {
    const parsed = JSON.parse(jsonString)
    return JSON.stringify(parsed, null, 2)
  } catch (e) {
    return false
  }
}

/**
 * 验证能力字段
 */
const validateCapabilityField = (capability, field) => {
  const value = assetForm.value[capability][field]
  const errorKey = `${capability.split('_')[0]}_${field}`
  
  // 如果能力被启用，验证字段
  if (assetForm.value[capability].enabled) {
    if (!value || (typeof value === 'string' && !value.trim())) {
      formErrors.value[errorKey] = `请输入${field === 'url' ? '服务URL' : '服务端口'}`
      return false
    }
    
    // 验证params字段
    if (field === 'params') {
      const validJson = validateJson(value)
      if (validJson === false) {
        formErrors.value[errorKey] = '请输入有效的JSON格式'
        return false
      }
      // 更新为格式化后的JSON
      assetForm.value[capability][field] = validJson
    }
    
    if (field === 'url') {
      try {
        new URL(value.startsWith('http') ? value : `http://${value}`)
      } catch {
        formErrors.value[errorKey] = '请输入有效的URL'
        return false
      }
    }
    
    if (field === 'port') {
      const port = Number(value)
      if (isNaN(port) || port < 1 || port > 65535) {
        formErrors.value[errorKey] = '端口范围为 1-65535'
        return false
      }
    }
  }
  
  delete formErrors.value[errorKey]
  return true
}

// 修改表单验证方法
const validateForm = () => {
  let isValid = true
  formErrors.value = {}

  // 验证基本字段
  Object.keys(formRules).forEach(field => {
    const rules = formRules[field]
    if (!rules) return

    for (const rule of rules) {
      // 检查条件验证规则
      if (rule.when && !rule.when(assetForm.value)) {
        continue
      }

      if (!validateField(field, assetForm.value[field])) {
        isValid = false
        break
      }
    }
  })

  // 验证 Lora 训练能力
  if (assetForm.value.lora_training.enabled) {
    if (!validateCapabilityField('lora_training', 'url')) isValid = false
    if (!validateCapabilityField('lora_training', 'port')) isValid = false
    if (!validateCapabilityField('lora_training', 'params')) isValid = false
  }

  // 验证 AI 引擎能力
  if (assetForm.value.ai_engine.enabled) {
    if (!validateCapabilityField('ai_engine', 'url')) isValid = false
    if (!validateCapabilityField('ai_engine', 'port')) isValid = false
  }

  return isValid
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

const openTerminal = (asset) => {
  selectedTerminalAsset.value = asset
  showTerminal.value = true
}

// 添加SSH验证状态
const isVerifyingSsh = ref(false)

// SSH连接验证方法
const verifySshConnection = async () => {
  // 验证必要字段
  if (!validateField('ip', assetForm.value.ip) || 
      !validateField('ssh_port', assetForm.value.ssh_port) ||
      !validateField('ssh_username', assetForm.value.ssh_username)) {
    return
  }

  if (assetForm.value.ssh_auth_type === 'PASSWORD' && 
      !validateField('ssh_password', assetForm.value.ssh_password)) {
    return
  }

  if (assetForm.value.ssh_auth_type === 'KEY' && 
      !validateField('ssh_key_path', assetForm.value.ssh_key_path)) {
    return
  }

  try {
    isVerifyingSsh.value = true
    
    // 构建验证数据
    const verifyData = {
      ip: assetForm.value.ip,
      ssh_port: assetForm.value.ssh_port,
      ssh_username: assetForm.value.ssh_username,
      ssh_auth_type: assetForm.value.ssh_auth_type,
      ssh_password: assetForm.value.ssh_password,
      ssh_key_path: assetForm.value.ssh_key_path
    }

    // 调用API验证SSH连接
    await assetApi.verifySshConnection(verifyData)
    message.success('SSH连接验证成功')
  } catch (error) {
    message.error(error.message || 'SSH连接验证失败')
  } finally {
    isVerifyingSsh.value = false
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
  padding: 16px;
  background: white;
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
  flex: 1;
  overflow: auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 24px;
  padding: 0 12px 12px;
}

/* 自定义滚动条样式 */
.assets-grid::-webkit-scrollbar {
  width: 8px;
}

.assets-grid::-webkit-scrollbar-track {
  background: transparent;
}

.assets-grid::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
}

.assets-grid::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.2);
}

.asset-card {
  display: flex;
  flex-direction: column;
  padding: 16px;
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid var(--border-color, rgba(0, 0, 0, 0.1));
  transition: all 0.2s ease;
  gap: 16px;
  cursor: pointer;
  max-height: 240px;
  min-height: 200px;
}

.asset-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.asset-card.is-selected {
  border: 2px solid var(--primary-color, #007AFF);
}

.asset-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.asset-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.asset-icon {
  width: 20px;
  height: 20px;
  color: var(--text-secondary, #8E8E93);
}

.asset-name {
  font-weight: 500;
  font-size: 15px;
  color: var(--text-primary, #1C1C1E);
}

.asset-status-badge {
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.asset-status-badge.connected {
  background: #E3F2FD;
  color: #1565C0;
}

.asset-status-badge.pending {
  background: #FFF3E0;
  color: #E65100;
}

.asset-status-badge.connection_error {
  background: #FFEBEE;
  color: #C62828;
}

.asset-card-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.info-grid {
  display: grid;
  gap: 12px;
  padding-right: 4px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-icon {
  width: 16px;
  height: 16px;
  color: var(--text-secondary, #8E8E93);
  flex-shrink: 0;
}

.info-text {
  font-size: 13px;
  color: var(--text-secondary, #8E8E93);
}

.capability-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.capability-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  background: var(--background-secondary, #F2F2F7);
  border-radius: 6px;
  font-size: 12px;
  color: var(--text-secondary, #8E8E93);
}

.capability-tag.is-verified {
  background: #E8F5E9;
  color: #2E7D32;
}

.tag-icon {
  width: 12px;
  height: 12px;
}

.asset-card-actions {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid var(--border-color, rgba(0, 0, 0, 0.1));
  margin-top: auto;
  flex-shrink: 0;
}

.mac-btn.small {
  padding: 6px;
  font-size: 12px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  transition: all 0.2s ease;
}

.verify-btn {
  background: #E3F2FD;
  color: #1565C0;
  border: none;
}

.verify-btn:hover {
  background: #BBDEFB;
}

.edit-btn {
  background: #F5F5F5;
  color: #424242;
  border: none;
}

.edit-btn:hover {
  background: #E0E0E0;
}

.delete-btn {
  background: #FFEBEE;
  color: #C62828;
  border: none;
}

.delete-btn:hover {
  background: #FFCDD2;
}

.btn-icon {
  width: 14px;
  height: 14px;
}

@media (max-width: 768px) {
  .asset-card {
    padding: 12px;
  }
  
  .asset-card-actions {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }
}

.asset-card-content::-webkit-scrollbar {
  width: 4px;
}

.asset-card-content::-webkit-scrollbar-track {
  background: transparent;
}

.asset-card-content::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 2px;
}

.asset-card-content::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.2);
}

/* 表单容器 */
.asset-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 4px;
}

/* 表单区块 */
.form-section {
  background: #F9F9F9;
  border-radius: 8px;
  padding: 20px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #1C1C1E;
  margin-bottom: 16px;
}

/* 表单项 */
.form-item {
  margin-bottom: 16px;
}

.form-item:last-child {
  margin-bottom: 0;
}

.form-item label {
  display: block;
  font-size: 13px;
  color: #6B7280;
  margin-bottom: 6px;
}

/* 输入框样式 */
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

/* 错误状态 */
.mac-input.is-error {
  border-color: #DC2626;
  background: #FEF2F2;
}

.mac-input.is-error:focus {
  box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.1);
}

/* 错误提示文字 */
.error-message {
  display: block;
  color: #DC2626;
  font-size: 12px;
  margin-top: 4px;
  line-height: 1.5;
}

/* 表单行布局 */
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

/* 文本域样式 */
.mac-textarea {
  width: 100%;
  min-height: 100px;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid #E5E7EB;
  background: #FFFFFF;
  color: #1C1C1E;
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
  transition: all 0.2s ease;
}

.mac-textarea:focus {
  outline: none;
  border-color: #007AFF;
  box-shadow: 0 0 0 2px rgba(0, 122, 255, 0.1);
}

.mac-textarea.is-error {
  border-color: #DC2626;
  background: #FEF2F2;
}

/* 能力区块头部 */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

/* 能力表单区域 */
.capability-form {
  background: #FFFFFF;
  border-radius: 6px;
  padding: 16px;
  margin-top: 12px;
}

/* 响应式调整 */
@media (max-width: 640px) {
  .form-row {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .form-section {
    padding: 16px;
  }
}

/* 必填项标记 */
.required-field label::after {
  content: '*';
  color: #DC2626;
  margin-left: 4px;
}

/* 表单验证提示动画 */
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4px); }
  75% { transform: translateX(4px); }
}

.is-error {
  animation: shake 0.3s ease-in-out;
}

/* 开关按钮容器 */
.switch-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

.switch-container label {
  margin-bottom: 0;
}

/* 占位符文本样式 */
.mac-input::placeholder,
.mac-textarea::placeholder {
  color: #A1A1AA;
}

/* 禁用状态样式 */
.mac-input:disabled,
.mac-textarea:disabled {
  background: #F3F4F6;
  cursor: not-allowed;
}

.terminal-btn {
  background: #F0F9FF;
  color: #0369A1;
  border: none;
}

.terminal-btn:hover {
  background: #E0F2FE;
}

.mac-input[type="password"] {
  font-family: monospace;
  letter-spacing: 0.2em;
}

select.mac-input {
  padding-right: 30px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%236B7280'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
  background-size: 16px;
  appearance: none;
  cursor: pointer;
}

select.mac-input:focus {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23007AFF'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
}

/* 添加过渡效果 */
.form-item {
  transition: all 0.3s ease;
}

.ssh-verify-section {
  position: relative;
}

.input-with-button {
  display: flex;
  gap: 8px;
}

.input-with-button .mac-input {
  flex: 1;
}

.verify-ssh-btn {
  padding: 0 12px;
  background: #F0F9FF;
  color: #0369A1;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.verify-ssh-btn:hover:not(:disabled) {
  background: #E0F2FE;
}

.verify-ssh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 加载动画 */
@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid #0369A1;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
</style> 