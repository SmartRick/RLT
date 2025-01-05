<template>
  <div class="materials-section">
    <div class="section-header">
      <h2>训练素材</h2>
      <div class="header-actions">
        <button class="add-btn" @click="showUploadDialog">
          <span class="icon">➕</span>
          添加素材
        </button>
      </div>
    </div>

    <div class="materials-grid">
      <div 
        v-for="material in materials" 
        :key="material.id" 
        class="material-card"
        :class="{ 'is-selected': selectedMaterial?.id === material.id }"
        @click="selectMaterial(material)"
      >
        <div class="material-header">
          <h3>{{ material.folder_name }}</h3>
          <span :class="['status-badge', material.status.toLowerCase()]">
            {{ material.status }}
          </span>
        </div>
        <div class="material-info">
          <p><strong>路径:</strong> {{ material.source_path }}</p>
          <p><strong>创建时间:</strong> {{ formatDate(material.created_at) }}</p>
          <p v-if="material.metadata">
            <strong>参数:</strong>
            <code>{{ JSON.stringify(material.metadata, null, 2) }}</code>
          </p>
        </div>
        <div class="material-actions">
          <button 
            class="action-btn"
            @click.stop="createTask(material)"
            :disabled="!canCreateTask(material)"
          >
            创建训练任务
          </button>
          <button 
            class="action-btn delete"
            @click.stop="confirmDelete(material)"
          >
            删除
          </button>
        </div>
      </div>
    </div>

    <!-- 上传对话框 -->
    <div v-if="showUpload" class="modal-overlay" @click="closeUploadDialog"></div>
    <div v-if="showUpload" class="modal upload-modal">
      <div class="modal-header">
        <h2>上传训练素材</h2>
        <button class="close-btn" @click="closeUploadDialog">×</button>
      </div>
      <div class="modal-body">
        <form @submit.prevent="handleUpload" class="upload-form">
          <div class="form-group">
            <label>文件夹名称</label>
            <input 
              v-model="uploadForm.folder_name"
              type="text"
              required
              placeholder="请输入文件夹名称"
            >
          </div>
          <div class="form-group">
            <label>源文件路径</label>
            <input 
              v-model="uploadForm.source_path"
              type="text"
              required
              placeholder="请输入源文件路径"
            >
          </div>
          <div class="form-group">
            <label>训练文件</label>
            <input 
              type="file"
              multiple
              @change="handleFileSelect"
              accept=".png,.jpg,.jpeg"
            >
          </div>
          <div class="form-group">
            <label>训练参数 (可选)</label>
            <textarea
              v-model="uploadForm.metadata"
              placeholder="请输入JSON格式的训练参数"
              rows="4"
            ></textarea>
          </div>
          <div class="form-actions">
            <button 
              type="submit"
              class="submit-btn"
              :disabled="isUploading"
            >
              {{ isUploading ? '上传中...' : '开始上传' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { trainingApi } from '@/api/training'

export default {
  name: 'MaterialList',
  setup() {
    const materials = ref([])
    const selectedMaterial = ref(null)
    const showUpload = ref(false)
    const isUploading = ref(false)
    const uploadForm = ref({
      folder_name: '',
      source_path: '',
      metadata: '',
      files: []
    })

    const loadMaterials = async () => {
      try {
        const response = await trainingApi.listMaterials()
        materials.value = response.data
      } catch (error) {
        console.error('加载训练素材失败:', error)
      }
    }

    const showUploadDialog = () => {
      showUpload.value = true
      uploadForm.value = {
        folder_name: '',
        source_path: '',
        metadata: '',
        files: []
      }
    }

    const closeUploadDialog = () => {
      showUpload.value = false
    }

    const handleFileSelect = (event) => {
      uploadForm.value.files = Array.from(event.target.files)
    }

    const handleUpload = async () => {
      if (!uploadForm.value.files.length) {
        alert('请选择要上传的文件')
        return
      }

      isUploading.value = true
      try {
        // 首先创建素材记录
        const materialResponse = await trainingApi.createMaterial({
          folder_name: uploadForm.value.folder_name,
          source_path: uploadForm.value.source_path,
          metadata: uploadForm.value.metadata ? JSON.parse(uploadForm.value.metadata) : null
        })

        // 然后上传文件
        const formData = new FormData()
        uploadForm.value.files.forEach(file => {
          formData.append('files', file)
        })

        await trainingApi.uploadMaterialFiles(materialResponse.data.id, formData)
        
        await loadMaterials()
        closeUploadDialog()
      } catch (error) {
        console.error('上传失败:', error)
        alert('上传失败: ' + error.message)
      } finally {
        isUploading.value = false
      }
    }

    const selectMaterial = (material) => {
      selectedMaterial.value = material
    }

    const canCreateTask = (material) => {
      return material.status === 'UPLOADED'
    }

    const createTask = async (material) => {
      try {
        await trainingApi.createTask({
          material_id: material.id,
          node_id: 1 // TODO: 允许选择训练节点
        })
        await loadMaterials()
      } catch (error) {
        console.error('创建任务失败:', error)
        alert('创建任务失败: ' + error.message)
      }
    }

    const confirmDelete = async (material) => {
      if (!confirm(`确定要删除素材 "${material.folder_name}" 吗？`)) {
        return
      }

      try {
        await trainingApi.deleteMaterial(material.id)
        await loadMaterials()
      } catch (error) {
        console.error('删除失败:', error)
        alert('删除失败: ' + error.message)
      }
    }

    const formatDate = (dateString) => {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString()
    }

    onMounted(() => {
      loadMaterials()
    })

    return {
      materials,
      selectedMaterial,
      showUpload,
      isUploading,
      uploadForm,
      showUploadDialog,
      closeUploadDialog,
      handleFileSelect,
      handleUpload,
      selectMaterial,
      canCreateTask,
      createTask,
      confirmDelete,
      formatDate
    }
  }
}
</script>

<style lang="scss" scoped>
.materials-section {
  padding: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.materials-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.material-card {
  background: var(--card-background);
  border-radius: var(--border-radius);
  padding: 15px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: transform var(--transition-speed);

  &:hover {
    transform: translateY(-2px);
  }

  &.is-selected {
    border: 2px solid var(--primary-color);
  }
}

.material-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8em;
  font-weight: bold;

  &.uploaded { background: var(--success-color); color: white; }
  &.processing { background: var(--warning-color); color: white; }
  &.failed { background: var(--error-color); color: white; }
}

.material-info {
  margin-bottom: 15px;
  
  code {
    display: block;
    background: rgba(0, 0, 0, 0.05);
    padding: 8px;
    border-radius: 4px;
    font-size: 0.9em;
    margin-top: 5px;
    white-space: pre-wrap;
  }
}

.material-actions {
  display: flex;
  gap: 10px;
  
  .action-btn {
    flex: 1;
    padding: 8px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: opacity var(--transition-speed);

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    &.delete {
      background: var(--error-color);
      color: white;
    }
  }
}

.upload-modal {
  width: 90%;
  max-width: 600px;
}

.upload-form {
  .form-group {
    margin-bottom: 15px;
  }

  textarea {
    width: 100%;
    font-family: monospace;
  }
}
</style> 