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
    rows: 24,  // 设置初始行数
    cols: 80   // 设置初始列数
  })

  // 添加插件
  fitAddon.value = new FitAddon()
  webLinksAddon.value = new WebLinksAddon()
  
  terminal.value.loadAddon(fitAddon.value)
  terminal.value.loadAddon(webLinksAddon.value)

  // 打开终端
  terminal.value.open(terminalRef.value)
  fitAddon.value.fit()

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
    terminal.value.writeln('Connected to terminal...')
    
    // 发送初始终端大小
    if (terminal.value) {
      const { rows, cols } = terminal.value
      socket.value.send(JSON.stringify({ type: 'resize', rows, cols }))
    }
  }
  
  // 添加 onmessage 处理器
  socket.value.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'error') {
        terminal.value?.writeln(`\r\nError: ${data.data}`)
        isConnected.value = false
      } else if (data.type === 'output') {
        // 处理换行符
        const text = data.data.replace(/\n/g, '\r\n')
        terminal.value?.write(text)
      }
    } catch (error) {
      // 如果不是JSON格式，直接写入终端
      console.error('Failed to parse message:', error)
      // 同样处理换行符
      const text = event.data.replace(/\n/g, '\r\n')
      terminal.value?.write(text)
    }
  }
  
  socket.value.onclose = () => {
    isConnected.value = false
    terminal.value?.writeln('\r\nConnection closed. Attempting to reconnect...')
    
    setTimeout(() => {
      if (show.value) {
        connectWebSocket()
      }
    }, 3000)
  }
  
  socket.value.onerror = (error) => {
    isConnected.value = false
    console.error('WebSocket error:', error)
    terminal.value?.writeln('\r\n连接错误: 请检查网络连接或服务器状态')
  }
  
  // 发送终端输入到服务器
  terminal.value.onData(data => {
    if (socket.value?.readyState === WebSocket.OPEN) {
      socket.value.send(JSON.stringify({ type: 'input', data }))
    }
  })
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
      // 只有在终端已经初始化并且插件已加载的情况下才尝试卸载插件
      if (isConnected.value) {
        if (fitAddon.value) {
          try {
            terminal.value.dispose()
          } catch (error) {
            console.debug('Fit addon cleanup error:', error)
          }
          fitAddon.value = null
        }
        
        if (webLinksAddon.value) {
          try {
            terminal.value.dispose()
          } catch (error) {
            console.debug('WebLinks addon cleanup error:', error)
          }
          webLinksAddon.value = null
        }
      }
      
      // 最后清理终端
      try {
        terminal.value.dispose()
      } catch (error) {
        console.debug('Terminal cleanup error:', error)
      }
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