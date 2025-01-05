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
            </div>
            <div class="log-viewer" ref="logViewer">
              <div v-if="!currentLog" class="no-log-selected">
                请选择要查看的日志文件
              </div>
              <pre v-else>{{ logContent.join('') }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, getCurrentInstance, onUnmounted } from 'vue'

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

    const loadLogFiles = async () => {
      try {
        const response = await proxy.$http.get('/api/logs')
        if (response.data.success) {
          logFiles.value = response.data.data
        }
      } catch (error) {
        console.error('获取日志列表失败:', error)
      }
    }

    const loadLogContent = async () => {
      if (!currentLog.value) return

      try {
        const response = await proxy.$http.get(`/api/logs/${currentLog.value}`, {
          params: { lines: logLines.value }
        })
        if (response.data.success) {
          const wasScrolledToBottom = isScrolledToBottom()
          logContent.value = response.data.data.content
          
          if (wasScrolledToBottom) {
            proxy.$nextTick(() => {
              scrollToBottom()
            })
          }
        }
      } catch (error) {
        console.error('读取日志内容失败:', error)
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

    // 组件卸载时清理定时器
    onUnmounted(() => {
      stopLogRefresh()
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
      formatFileSize
    }
  },
  mounted() {
    this.loadLogFiles()
  }
}
</script> 