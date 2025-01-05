<template>
  <div class="assets-container">
    <!-- 顶部操作栏 -->
    <div class="action-bar mac-card">
      <div class="search-box">
        <input 
          type="text" 
          v-model="searchQuery"
          placeholder="搜索资产..." 
          class="mac-input"
        >
      </div>
      <button class="mac-btn primary" @click="showCreateModal = true">
        <i class="icon-plus"></i> 新建资产 ✨
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
          <span class="asset-name">{{ asset.name }}</span>
          <span class="asset-type">{{ asset.type }}</span>
        </div>
        
        <div class="asset-info">
          <div class="info-item">
            <i class="icon-calendar"></i>
            <span>{{ formatDate(asset.created_at) }}</span>
          </div>
          <div class="info-item">
            <i class="icon-file"></i>
            <span>{{ asset.file_count }} 个文件</span>
          </div>
        </div>
        
        <div class="asset-actions">
          <button class="mac-btn small" @click.stop="showUploadModal(asset)">
            上传 📤
          </button>
          <button class="mac-btn small danger" @click.stop="confirmDelete(asset)">
            删除 🗑️
          </button>
        </div>
      </div>
    </div>

    <!-- 新建资产弹窗 -->
    <modal v-model="showCreateModal" title="新建资产 🎨">
      <template #body>
        <form @submit.prevent="createAsset" class="create-form">
          <div class="form-item">
            <label>资产名称</label>
            <input v-model="newAsset.name" class="mac-input" required>
          </div>
          <div class="form-item">
            <label>资产类型</label>
            <select v-model="newAsset.type" class="mac-select" required>
              <option value="image">图片</option>
              <option value="video">视频</option>
              <option value="audio">音频</option>
            </select>
          </div>
          <div class="form-item">
            <label>描述</label>
            <textarea v-model="newAsset.description" class="mac-textarea"></textarea>
          </div>
        </form>
      </template>
      <template #footer>
        <button class="mac-btn" @click="showCreateModal = false">取消</button>
        <button class="mac-btn primary" @click="createAsset">创建</button>
      </template>
    </modal>

    <!-- 上传文件弹窗 -->
    <modal v-model="showUploadModal" title="上传文件 📁">
      <template #body>
        <div class="upload-area" 
             @drop.prevent="handleFileDrop"
             @dragover.prevent
             @dragenter.prevent>
          <div class="upload-hint">
            <i class="icon-upload"></i>
            <p>拖拽文件到此处或点击上传</p>
          </div>
          <input type="file" 
                 ref="fileInput"
                 multiple
                 @change="handleFileSelect"
                 style="display: none">
        </div>
        <div class="upload-list" v-if="uploadFiles.length">
          <div v-for="(file, index) in uploadFiles" 
               :key="index"
               class="upload-item">
            <span>{{ file.name }}</span>
            <div class="progress-bar">
              <div class="progress" :style="{width: file.progress + '%'}"></div>
            </div>
          </div>
        </div>
      </template>
    </modal>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import Modal from '@/components/common/Modal.vue'
import { formatDate } from '@/utils/date'

export default {
  name: 'Assets',
  components: { Modal },
  
  setup() {
    const assets = ref([])
    const searchQuery = ref('')
    const selectedAsset = ref(null)
    const showCreateModal = ref(false)
    const showUploadModal = ref(false)
    const uploadFiles = ref([])
    
    const newAsset = ref({
      name: '',
      type: 'image',
      description: ''
    })

    // 过滤资产列表
    const filteredAssets = computed(() => {
      if (!searchQuery.value) return assets.value
      const query = searchQuery.value.toLowerCase()
      return assets.value.filter(asset => 
        asset.name.toLowerCase().includes(query) ||
        asset.type.toLowerCase().includes(query)
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

    // 创建新资产
    const createAsset = async () => {
      try {
        const response = await fetch('/api/v1/assets', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(newAsset.value)
        })
        
        if (response.ok) {
          showCreateModal.value = false
          await fetchAssets()
          newAsset.value = { name: '', type: 'image', description: '' }
        }
      } catch (error) {
        console.error('创建资产失败:', error)
      }
    }

    // 处理文件上传
    const handleFileUpload = async (files) => {
      const formData = new FormData()
      files.forEach(file => {
        formData.append('files', file)
      })

      try {
        const response = await fetch(`/api/v1/assets/${selectedAsset.value.id}/upload`, {
          method: 'POST',
          body: formData
        })
        
        if (response.ok) {
          showUploadModal.value = false
          await fetchAssets()
        }
      } catch (error) {
        console.error('上传文件失败:', error)
      }
    }

    return {
      assets,
      searchQuery,
      selectedAsset,
      showCreateModal,
      showUploadModal,
      uploadFiles,
      newAsset,
      filteredAssets,
      formatDate,
      createAsset,
      handleFileUpload
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
</style> 