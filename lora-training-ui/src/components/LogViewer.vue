<template>
  <div>
    <div class="modal-overlay" @click="$emit('close')"></div>
    <div class="modal logs-modal">
      <div class="modal-header">
        <h2>日志查看</h2>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>
      <div class="modal-body">
        <div class="logs-container">
          <div class="log-files">
            <div class="log-files-header">
              <h3>日志文件</h3>
              <div class="refresh-indicator" :class="{ spinning: filesLoading }">🔄</div>
            </div>
            <div 
              v-for="log in logFiles" 
              :key="log.filename"
              :class="['log-file', { active: currentLog === log.filename }]"
              @click="selectLog(log.filename)"
            >
              <div class="log-file-name">{{ log.filename }}</div>
              <div class="log-file-info">
                <span>{{ formatDate(log.modified) }}</span>
                <span>{{ formatFileSize(log.size) }}</span>
              </div>
            </div>
          </div>
          <div class="log-content">
            <div class="log-controls">
              <select v-model="logLines" @change="loadLogContent">
                <option value="100">最近100行</option>
                <option value="500">最近500行</option>
                <option value="1000">最近1000行</option>
                <option value="5000">最近5000行</option>
              </select>
              <button 
                class="refresh-btn"
                @click="loadLogContent"
                :disabled="!currentLog"
              >
                刷新
              </button>
              <button 
                class="auto-refresh-btn"
                :class="{ active: logAutoRefresh }"
                @click="toggleAutoRefresh"
                :disabled="!currentLog"
              >
                自动刷新
              </button>
              <div class="scroll-controls">
                <button 
                  class="scroll-btn"
                  @click="scrollToBottom"
                  :disabled="!currentLog"
                >
                  滚动到底部
                </button>
              </div>
              <div class="loading-indicator" v-if="loading">加载中...</div>
            </div>
            <div class="log-viewer" ref="logViewer">
              <div v-if="!currentLog" class="no-log-selected">
                请选择要查看的日志文件
              </div>
              <template v-else>
                <div v-if="loading" class="loading-overlay">
                  <div class="spinner"></div>
                </div>
                <pre>{{ logContent.join('') }}</pre>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, getCurrentInstance, onMounted, onUnmounted } from 'vue'

export default {
  name: 'LogViewer',
  setup() {
    const { proxy } = getCurrentInstance()
    const logFiles = ref([])
    const currentLog = ref(null)
    const logContent = ref([])
    const logLines = ref("100")
    const logAutoRefresh = ref(false)
    const logRefreshInterval = ref(null)
    const logViewer = ref(null)
    const loading = ref(false)
    const filesLoading = ref(false)
    const error = ref('')
    const fileListRefreshInterval = ref(null)

    const loadLogFiles = async () => {
      filesLoading.value = true
      try {
        const response = await proxy.$http.get('/api/logs')
        if (response.data.success) {
          logFiles.value = response.data.data
          error.value = ''
        }
      } catch (err) {
        console.error('获取日志列表失败:', err)
        error.value = '获取日志列表失败'
      } finally {
        filesLoading.value = false
      }
    }

    const loadLogContent = async () => {
      if (!currentLog.value) return
      loading.value = true
      try {
        const response = await proxy.$http.get(`/api/logs/${currentLog.value}`, {
          params: { lines: logLines.value }
        })
        if (response.data.success) {
          const wasScrolledToBottom = isScrolledToBottom()
          logContent.value = response.data.data.content
          error.value = ''
          
          if (wasScrolledToBottom) {
            proxy.$nextTick(() => {
              scrollToBottom()
            })
          }
        }
      } catch (err) {
        console.error('读取日志内容失败:', err)
        error.value = '读取日志内容失败'
      } finally {
        loading.value = false
      }
    }

    const selectLog = (filename) => {
      currentLog.value = filename
      loadLogContent()
      if (logAutoRefresh.value) {
        startLogRefresh()
      }
    }

    const toggleAutoRefresh = () => {
      logAutoRefresh.value = !logAutoRefresh.value
      if (logAutoRefresh.value) {
        startLogRefresh()
      } else {
        stopLogRefresh()
      }
    }

    const startLogRefresh = () => {
      loadLogContent() // 立即刷新一次
      stopLogRefresh() // 清除可能存在的旧定时器
      logRefreshInterval.value = setInterval(() => {
        loadLogContent()
      }, 5000) // 每5秒刷新一次
    }

    const stopLogRefresh = () => {
      if (logRefreshInterval.value) {
        clearInterval(logRefreshInterval.value)
        logRefreshInterval.value = null
      }
    }

    const isScrolledToBottom = () => {
      const viewer = logViewer.value
      if (!viewer) return false
      return Math.abs(viewer.scrollHeight - viewer.scrollTop - viewer.clientHeight) < 1
    }

    const scrollToBottom = () => {
      const viewer = logViewer.value
      if (viewer) {
        viewer.scrollTop = viewer.scrollHeight
      }
    }

    const formatDate = (dateString) => {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString()
    }

    const formatFileSize = (bytes) => {
      const units = ['B', 'KB', 'MB', 'GB']
      let size = bytes
      let unitIndex = 0
      
      while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024
        unitIndex++
      }
      
      return `${size.toFixed(1)} ${units[unitIndex]}`
    }

    const startFileListRefresh = () => {
      stopFileListRefresh()
      fileListRefreshInterval.value = setInterval(() => {
        loadLogFiles()
      }, 30000) // 每30秒刷新一次文件列表
    }

    const stopFileListRefresh = () => {
      if (fileListRefreshInterval.value) {
        clearInterval(fileListRefreshInterval.value)
        fileListRefreshInterval.value = null
      }
    }

    onMounted(() => {
      loadLogFiles()
      startFileListRefresh()
    })

    onUnmounted(() => {
      stopLogRefresh()
      stopFileListRefresh()
    })

    return {
      logFiles,
      currentLog,
      logContent,
      logLines,
      logAutoRefresh,
      logViewer,
      loadLogFiles,
      loadLogContent,
      selectLog,
      toggleAutoRefresh,
      scrollToBottom,
      formatDate,
      formatFileSize,
      loading,
      filesLoading,
      error
    }
  }
}
</script>

<style lang="scss" scoped>
.loading-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 0.9em;
}

.refresh-indicator {
  cursor: pointer;
  transition: transform 0.3s ease;
  
  &.spinning {
    animation: spin 1s linear infinite;
  }
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--background-color);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.log-scroller {
  height: 100%;
  overflow-y: auto;
}

.log-line {
  padding: 2px 10px;
  font-family: monospace;
  white-space: pre-wrap;
  word-wrap: break-word;
  
  &:hover {
    background: rgba(0, 0, 0, 0.03);
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@media (prefers-color-scheme: dark) {
  .loading-overlay {
    background: rgba(0, 0, 0, 0.8);
  }
  
  .log-line:hover {
    background: rgba(255, 255, 255, 0.03);
  }
}
</style> 