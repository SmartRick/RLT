<template>
  <BaseModal
    v-model="show"
    :title="`终端 - ${asset?.name}`"
    size="large"
    @close="handleClose"
  >
    <template #body>
      <div class="terminal-container" ref="terminalRef"></div>
    </template>
  </BaseModal>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, watch, nextTick } from 'vue'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import { WebLinksAddon } from 'xterm-addon-web-links'
import BaseModal from '@/components/common/Modal.vue'
import 'xterm/css/xterm.css'

const props = defineProps({
  modelValue: Boolean,
  asset: Object
})

const emit = defineEmits(['update:modelValue'])

const show = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const terminalRef = ref(null)
const terminal = ref(null)
const socket = ref(null)
const fitAddon = ref(null)
const webLinksAddon = ref(null)

// 添加连接状态标志
const isConnected = ref(false)

onMounted(() => {
  if (show.value) {
    initTerminal()
  }
})

// 监听显示状态变化
watch(show, (newVal) => {
  if (newVal) {
    nextTick(() => {
      initTerminal()
    })
  } else {
    cleanupTerminal()
  }
})

onBeforeUnmount(() => {
  cleanupTerminal()
})

const initTerminal = () => {
  if (!terminalRef.value || !props.asset?.id) return
  
  // 确保清理之前的终端
  cleanupTerminal()
  
  // 初始化终端
  terminal.value = new Terminal({
    fontSize: 14,
    fontFamily: 'Menlo, Monaco, "Courier New", monospace',
    theme: {
      background: '#1E1E1E',
      foreground: '#D4D4D4'
    },
    cursorBlink: true,
    rows: 24,
    cols: 80,
    scrollback: 1000,  // 添加滚动历史
    convertEol: true   // 确保换行符正确处理
  })

  // 添加插件
  fitAddon.value = new FitAddon()
  webLinksAddon.value = new WebLinksAddon()
  
  terminal.value.loadAddon(fitAddon.value)
  terminal.value.loadAddon(webLinksAddon.value)

  // 打开终端
  terminal.value.open(terminalRef.value)
  fitAddon.value.fit()

  // 添加窗口大小变化监听
  const resizeHandler = () => {
    if (fitAddon.value && terminal.value && socket.value?.readyState === WebSocket.OPEN) {
      fitAddon.value.fit()
      const { rows, cols } = terminal.value
      socket.value.send(JSON.stringify({ type: 'resize', rows, cols }))
    }
  }
  
  window.addEventListener('resize', resizeHandler)
  
  // 在组件卸载时移除监听器
  onBeforeUnmount(() => {
    window.removeEventListener('resize', resizeHandler)
  })

  // 连接WebSocket
  connectWebSocket()
}

const connectWebSocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  if (!props.asset?.id) {
    console.error('Asset ID is missing')
    return
  }
  
  const wsUrl = `${protocol}//${window.location.host}/api/v1/terminal/${props.asset.id}`
  console.log('Connecting to WebSocket:', wsUrl)
  
  socket.value = new WebSocket(wsUrl)
  
  socket.value.onopen = () => {
    isConnected.value = true
    terminal.value?.clear()  // 清除之前的内容
    
    // 发送初始终端大小
    if (terminal.value) {
      const { rows, cols } = terminal.value
      socket.value.send(JSON.stringify({ type: 'resize', rows, cols }))
    }
  }
  
  socket.value.onmessage = (event) => {
    try {
      console.debug('Received message:', event.data)  // 调试日志
      const data = JSON.parse(event.data)
      if (data.type === 'error') {
        terminal.value?.writeln(`\r\n\x1b[31mError: ${data.data}\x1b[0m`)  // 红色显示错误
        isConnected.value = false
      } else if (data.type === 'output') {
        terminal.value?.write(data.data)
      }
    } catch (error) {
      console.error('Failed to parse message:', error)
      // 如果解析失败，尝试直接写入数据
      terminal.value?.write(event.data)
    }
  }
  
  socket.value.onclose = () => {
    isConnected.value = false
    terminal.value?.writeln('\r\n\x1b[33mConnection closed. Attempting to reconnect...\x1b[0m')  // 黄色显示重连信息
    
    setTimeout(() => {
      if (show.value) {
        connectWebSocket()
      }
    }, 3000)
  }
  
  socket.value.onerror = (error) => {
    isConnected.value = false
    console.error('WebSocket error:', error)
    terminal.value?.writeln('\r\n\x1b[31m连接错误: 请检查网络连接或服务器状态\x1b[0m')  // 红色显示错误
  }
  
  // 处理终端输入
  if (terminal.value) {
    terminal.value.onData(data => {
      if (socket.value?.readyState === WebSocket.OPEN) {
        socket.value.send(JSON.stringify({ type: 'input', data }))
      }
    })
  }
}

const cleanupTerminal = () => {
  try {
    // 先关闭 WebSocket 连接
    if (socket.value) {
      socket.value.close()
      socket.value = null
    }
    
    // 清理终端和插件
    if (terminal.value) {
      if (fitAddon.value) {
        fitAddon.value.dispose()
        fitAddon.value = null
      }
      
      if (webLinksAddon.value) {
        webLinksAddon.value.dispose()
        webLinksAddon.value = null
      }
      
      terminal.value.dispose()
      terminal.value = null
    }
  } catch (error) {
    console.error('Terminal cleanup failed:', error)
  } finally {
    isConnected.value = false
  }
}

const handleClose = () => {
  cleanupTerminal()
  show.value = false
}
</script>

<style scoped>
.terminal-container {
  width: 100%;
  height: 480px;
  background: #1E1E1E;
  border-radius: 6px;
  overflow: hidden;
  padding: 4px;
}
</style> 