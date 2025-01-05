<template>
  <div class="materials-view">
    <div class="actions">
      <button class="add-btn" @click="openUploadDialog">
        <span class="icon">➕</span>
        添加素材
      </button>
    </div>

    <div class="materials-grid">
      <div 
        v-for="material in materials" 
        :key="material.id" 
        class="material-card"
      >
        <div class="material-header">
          <h3>{{ material.name }}</h3>
          <span :class="['status-badge', material.status.toLowerCase()]">
            {{ material.status }}
          </span>
        </div>
        <div class="material-info">
          <p>
            <strong>文件夹:</strong>
            <span>{{ material.folder_name }}</span>
          </p>
          <p>
            <strong>创建时间:</strong>
            <span>{{ formatDate(material.created_at) }}</span>
          </p>
          <p>
            <strong>文件数量:</strong>
            <span>{{ material.file_count || 0 }}</span>
          </p>
          <p v-if="material.error" class="error-message">
            <strong>错误信息:</strong>
            <span>{{ material.error }}</span>
          </p>
        </div>
        <div class="material-actions">
          <button 
            class="action-btn upload"
            @click="uploadFiles(material)"
            v-if="material.status === 'PENDING'"
          >
            上传文件
          </button>
          <button 
            class="action-btn edit"
            @click="editMaterial(material)"
          >
            编辑
          </button>
          <button 
            class="action-btn delete"
            @click="confirmDelete(material)"
          >
            删除
          </button>
        </div>
      </div>
    </div>

    <!-- 添加/编辑素材对话框 -->
    <div v-if="showDialog" class="modal-overlay" @click="closeDialog"></div>
    <div v-if="showDialog" class="modal material-modal">
      <div class="modal-header">
        <h2>{{ editingMaterial ? '编辑素材' : '添加素材' }}</h2>
        <button class="close-btn" @click="closeDialog">×</button>
      </div>
      <div class="modal-body">
        <form @submit.prevent="handleSubmit" class="material-form">
          <div class="form-group">
            <label>名称</label>
            <input 
              type="text" 
              v-model="form.name"
              required
              placeholder="请输入素材名称"
            >
          </div>
          <div class="form-group">
            <label>文件夹名</label>
            <input 
              type="text" 
              v-model="form.folder_name"
              required
              placeholder="请输入文件夹名称"
            >
          </div>
          <div class="form-actions">
            <button 
              type="submit" 
              class="submit-btn"
              :disabled="submitting"
            >
              {{ submitting ? '保存中...' : '保存' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 文件上传对话框 -->
    <div v-if="showUploadDialog" class="modal-overlay" @click="closeUploadDialog"></div>
    <div v-if="showUploadDialog" class="modal upload-modal">
      <div class="modal-header">
        <h2>上传文件</h2>
        <button class="close-btn" @click="closeUploadDialog">×</button>
      </div>
      <div class="modal-body">
        <div class="upload-form">
          <input 
            type="file" 
            ref="fileInput"
            multiple
            @change="handleFileSelect"
          >
          <div class="upload-list" v-if="selectedFiles.length">
            <div 
              v-for="(file, index) in selectedFiles"
              :key="index"
              class="upload-item"
            >
              <span class="file-name">{{ file.name }}</span>
              <span class="file-size">{{ formatFileSize(file.size) }}</span>
            </div>
          </div>
          <div class="upload-actions">
            <button 
              class="upload-btn"
              @click="startUpload"
              :disabled="uploading || !selectedFiles.length"
            >
              {{ uploading ? '上传中...' : '开始上传' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 确认删除对话框 -->
    <ConfirmDialog
      v-if="showDeleteConfirm"
      title="删除素材"
      :message="confirmMessage"
      :dangerous="true"
      @confirm="deleteMaterial"
      @cancel="cancelDelete"
    />
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { trainingApi } from '@/api/training'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'

export default {
  name: 'MaterialsView',
  components: {
    ConfirmDialog
  },
  setup() {
    const materials = ref([])
    const showDialog = ref(false)
    const showUploadDialog = ref(false)
    const showDeleteConfirm = ref(false)
    const editingMaterial = ref(null)
    const materialToDelete = ref(null)
    const submitting = ref(false)
    const uploading = ref(false)
    const selectedFiles = ref([])
    const form = ref({
      name: '',
      folder_name: ''
    })

    const confirmMessage = computed(() => {
      if (!materialToDelete.value) return ''
      return `确定要删除素材 "${materialToDelete.value.name}" 吗？此操作不可恢复。`
    })

    const loadMaterials = async () => {
      try {
        const response = await trainingApi.listMaterials()
        materials.value = response.data
      } catch (error) {
        console.error('加载素材失败:', error)
      }
    }

    const openUploadDialog = () => {
      editingMaterial.value = null
      form.value = {
        name: '',
        folder_name: ''
      }
      showDialog.value = true
    }

    const closeDialog = () => {
      showDialog.value = false
      editingMaterial.value = null
    }

    const closeUploadDialog = () => {
      showUploadDialog.value = false
      selectedFiles.value = []
    }

    const handleFileSelect = (event) => {
      selectedFiles.value = Array.from(event.target.files)
    }

    const startUpload = async () => {
      if (!selectedFiles.value.length) return

      uploading.value = true
      try {
        const formData = new FormData()
        selectedFiles.value.forEach(file => {
          formData.append('files', file)
        })
        await trainingApi.uploadMaterialFiles(editingMaterial.value.id, formData)
        await loadMaterials()
        closeUploadDialog()
      } catch (error) {
        console.error('上传文件失败:', error)
      } finally {
        uploading.value = false
      }
    }

    const handleSubmit = async () => {
      submitting.value = true
      try {
        if (editingMaterial.value) {
          await trainingApi.updateMaterial(editingMaterial.value.id, form.value)
        } else {
          await trainingApi.createMaterial(form.value)
        }
        await loadMaterials()
        closeDialog()
      } catch (error) {
        console.error('保存素材失败:', error)
      } finally {
        submitting.value = false
      }
    }

    const editMaterial = (material) => {
      editingMaterial.value = material
      form.value = {
        name: material.name,
        folder_name: material.folder_name
      }
      showDialog.value = true
    }

    const confirmDelete = (material) => {
      materialToDelete.value = material
      showDeleteConfirm.value = true
    }

    const deleteMaterial = async () => {
      try {
        await trainingApi.deleteMaterial(materialToDelete.value.id)
        await loadMaterials()
      } catch (error) {
        console.error('删除素材失败:', error)
      } finally {
        showDeleteConfirm.value = false
        materialToDelete.value = null
      }
    }

    const cancelDelete = () => {
      showDeleteConfirm.value = false
      materialToDelete.value = null
    }

    const formatDate = (dateString) => {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString()
    }

    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`
    }

    onMounted(() => {
      loadMaterials()
    })

    return {
      materials,
      showDialog,
      showUploadDialog,
      showDeleteConfirm,
      editingMaterial,
      materialToDelete,
      submitting,
      uploading,
      selectedFiles,
      form,
      openUploadDialog,
      closeDialog,
      closeUploadDialog,
      handleFileSelect,
      startUpload,
      handleSubmit,
      editMaterial,
      confirmDelete,
      deleteMaterial,
      cancelDelete,
      formatDate,
      formatFileSize,
      confirmMessage,
    }
  }
}
</script>

<style lang="scss" scoped>
.materials-view {
  padding: 20px;
}

.actions {
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
}

.material-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;

  h3 {
    margin: 0;
    font-size: 1.1em;
  }
}

.material-info {
  margin-bottom: 15px;

  p {
    margin: 8px 0;
    display: flex;
    gap: 10px;

    strong {
      min-width: 80px;
    }
  }

  .error-message {
    color: var(--error-color);
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
    transition: opacity 0.2s;

    &:hover {
      opacity: 0.8;
    }

    &.upload { background: var(--primary-color); color: white; }
    &.edit { background: var(--warning-color); color: white; }
    &.delete { background: var(--error-color); color: white; }
  }
}

.material-modal {
  width: 90%;
  max-width: 500px;
}

.upload-modal {
  width: 90%;
  max-width: 600px;
}

.upload-form {
  .upload-list {
    margin: 15px 0;
    max-height: 300px;
    overflow-y: auto;
  }

  .upload-item {
    display: flex;
    justify-content: space-between;
    padding: 8px;
    border-bottom: 1px solid var(--border-color);

    &:last-child {
      border-bottom: none;
    }
  }

  .upload-actions {
    margin-top: 15px;
    text-align: right;
  }
}
</style> 