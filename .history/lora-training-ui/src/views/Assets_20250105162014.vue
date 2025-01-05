<template>
  <div class="assets-view">
    <div class="actions">
      <button class="add-btn" @click="showAddAssetDialog">
        <span class="icon">➕</span>
        添加资产
      </button>
    </div>

    <div class="assets-grid">
      <div 
        v-for="asset in assets" 
        :key="asset.id" 
        class="asset-card"
      >
        <div class="asset-header">
          <h3>{{ asset.name }}</h3>
          <span :class="['status-badge', asset.status.toLowerCase()]">
            {{ asset.status }}
          </span>
        </div>
        <div class="asset-info">
          <p>
            <strong>类型:</strong>
            <span>{{ asset.type }}</span>
          </p>
          <p>
            <strong>IP地址:</strong>
            <span>{{ asset.ip }}</span>
          </p>
          <p>
            <strong>SSH端口:</strong>
            <span>{{ asset.ssh_port }}</span>
          </p>
          <p>
            <strong>用户名:</strong>
            <span>{{ asset.ssh_username }}</span>
          </p>
          <p>
            <strong>密钥路径:</strong>
            <span>{{ asset.ssh_key_path }}</span>
          </p>
        </div>
        <div class="asset-actions">
          <button 
            class="action-btn test"
            @click="testConnection(asset)"
            :disabled="testing === asset.id"
          >
            {{ testing === asset.id ? '测试中...' : '测试连接' }}
          </button>
          <button 
            class="action-btn edit"
            @click="editAsset(asset)"
          >
            编辑
          </button>
          <button 
            class="action-btn delete"
            @click="confirmDelete(asset)"
          >
            删除
          </button>
        </div>
      </div>
    </div>

    <!-- 添加/编辑资产对话框 -->
    <div v-if="showDialog" class="modal-overlay" @click="closeDialog"></div>
    <div v-if="showDialog" class="modal asset-modal">
      <div class="modal-header">
        <h2>{{ editingAsset ? '编辑资产' : '添加资产' }}</h2>
        <button class="close-btn" @click="closeDialog">×</button>
      </div>
      <div class="modal-body">
        <form @submit.prevent="handleSubmit" class="asset-form">
          <div class="form-group">
            <label>名称</label>
            <input 
              v-model="form.name"
              type="text"
              required
              placeholder="请输入资产名称"
            >
          </div>
          <div class="form-group">
            <label>类型</label>
            <select v-model="form.type" required>
              <option value="TRAINING_NODE">训练节点</option>
              <option value="AI_NODE">AI节点</option>
            </select>
          </div>
          <div class="form-group">
            <label>IP地址</label>
            <input 
              v-model="form.ip"
              type="text"
              required
              placeholder="请输入IP地址"
            >
          </div>
          <div class="form-group">
            <label>SSH端口</label>
            <input 
              v-model.number="form.ssh_port"
              type="number"
              required
              min="1"
              max="65535"
              placeholder="22"
            >
          </div>
          <div class="form-group">
            <label>SSH用户名</label>
            <input 
              v-model="form.ssh_username"
              type="text"
              required
              placeholder="请输入SSH用户名"
            >
          </div>
          <div class="form-group">
            <label>SSH密钥路径</label>
            <input 
              v-model="form.ssh_key_path"
              type="text"
              placeholder="~/.ssh/id_rsa"
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
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { assetApi } from '@/api/asset'

export default {
  name: 'Assets',
  setup() {
    const assets = ref([])
    const showDialog = ref(false)
    const editingAsset = ref(null)
    const submitting = ref(false)
    const testing = ref(null)
    const form = reactive({
      name: '',
      type: 'TRAINING_NODE',
      ip: '',
      ssh_port: 22,
      ssh_username: '',
      ssh_key_path: ''
    })

    const loadAssets = async () => {
      try {
        const response = await assetApi.list()
        assets.value = response.data
      } catch (error) {
        console.error('加载资产失败:', error)
      }
    }

    const showAddAssetDialog = () => {
      editingAsset.value = null
      Object.assign(form, {
        name: '',
        type: 'TRAINING_NODE',
        ip: '',
        ssh_port: 22,
        ssh_username: '',
        ssh_key_path: ''
      })
      showDialog.value = true
    }

    const editAsset = (asset) => {
      editingAsset.value = asset
      Object.assign(form, asset)
      showDialog.value = true
    }

    const closeDialog = () => {
      showDialog.value = false
      editingAsset.value = null
    }

    const handleSubmit = async () => {
      submitting.value = true
      try {
        if (editingAsset.value) {
          await assetApi.update(editingAsset.value.id, form)
        } else {
          await assetApi.create(form)
        }
        await loadAssets()
        closeDialog()
      } catch (error) {
        console.error('保存资产失败:', error)
      } finally {
        submitting.value = false
      }
    }

    const testConnection = async (asset) => {
      testing.value = asset.id
      try {
        await assetApi.testConnection(asset.id)
        alert('连接测试成功!')
      } catch (error) {
        alert(`连接测试失败: ${error.response?.data?.detail || error.message}`)
      } finally {
        testing.value = null
      }
    }

    const confirmDelete = async (asset) => {
      if (!confirm(`确定要删除资产 "${asset.name}" 吗？`)) {
        return
      }

      try {
        await assetApi.delete(asset.id)
        await loadAssets()
      } catch (error) {
        console.error('删除资产失败:', error)
      }
    }

    // 初始加载
    loadAssets()

    return {
      assets,
      showDialog,
      editingAsset,
      submitting,
      testing,
      form,
      showAddAssetDialog,
      editAsset,
      closeDialog,
      handleSubmit,
      testConnection,
      confirmDelete
    }
  }
}
</script>

<style lang="scss" scoped>
.assets-view {
  padding: 20px;
}

.actions {
  margin-bottom: 20px;
}

.assets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.asset-card {
  background: var(--card-background);
  border-radius: var(--border-radius);
  padding: 15px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.asset-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;

  h3 {
    margin: 0;
    font-size: 1.2em;
  }
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8em;
  font-weight: bold;

  &.online { background: var(--success-color); color: white; }
  &.offline { background: var(--error-color); color: white; }
}

.asset-info {
  margin-bottom: 15px;

  p {
    margin: 8px 0;
    display: flex;
    gap: 10px;

    strong {
      min-width: 80px;
    }
  }
}

.asset-actions {
  display: flex;
  gap: 10px;

  .action-btn {
    flex: 1;
    padding: 8px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: opacity 0.2s;

    &:hover:not(:disabled) {
      opacity: 0.8;
    }

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    &.test { background: var(--primary-color); color: white; }
    &.edit { background: var(--warning-color); color: white; }
    &.delete { background: var(--error-color); color: white; }
  }
}

.asset-modal {
  width: 90%;
  max-width: 500px;
}

.asset-form {
  .form-group {
    margin-bottom: 15px;

    label {
      display: block;
      margin-bottom: 5px;
      font-weight: 500;
    }

    input, select {
      width: 100%;
      padding: 8px;
      border: 1px solid var(--border-color);
      border-radius: var(--border-radius);
      background: var(--input-background);
      color: var(--text-color);
    }
  }
}
</style> 