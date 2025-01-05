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
  }
})

onBeforeUnmount(() => {
  cleanupTerminal()
})

const initTerminal = () => {
  if (!terminalRef.value) return
  
  // 初始化终端
  terminal.value = new Terminal({
    fontSize: 14,
    fontFamily: 'Menlo, Monaco, "Courier New", monospace',
    theme: {
      background: '#1E1E1E',
      foreground: '#D4D4D4'
    },
    cursorBlink: true
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

  // 监听窗口大小变化
  const resizeHandler = () => {
    if (fitAddon.value) {
      fitAddon.value.fit()
      // 发送新的终端大小到服务器
      if (socket.value?.readyState === WebSocket.OPEN) {
        const { rows, cols } = terminal.value
        socket.value.send(JSON.stringify({ type: 'resize', rows, cols }))
      }
    }
  }
  
  window.addEventListener('resize', resizeHandler)
  
  // 清理函数
  onBeforeUnmount(() => {
    window.removeEventListener('resize', resizeHandler)
  })
}

const connectWebSocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/api/terminal/${props.asset.id}`
  
  socket.value = new WebSocket(wsUrl)
  
  socket.value.onopen = () => {
    terminal.value.writeln('Connected to terminal...')
    // 发送初始终端大小
    const { rows, cols } = terminal.value
    socket.value.send(JSON.stringify({ type: 'resize', rows, cols }))
  }
  
  socket.value.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'output') {
        terminal.value.write(data.data)
      }
    } catch {
      // 如果不是JSON格式，直接写入终端
      terminal.value.write(event.data)
    }
  }
  
  socket.value.onclose = () => {
    terminal.value.writeln('\r\nConnection closed.')
  }
  
  socket.value.onerror = (error) => {
    terminal.value.writeln(`\r\nWebSocket error: ${error.message}`)
  }
  
  // 发送终端输入到服务器
  terminal.value.onData(data => {
    if (socket.value && socket.value.readyState === WebSocket.OPEN) {
      socket.value.send(JSON.stringify({ type: 'input', data }))
    }
  })
}

const cleanupTerminal = () => {
  if (socket.value) {
    socket.value.close()
    socket.value = null
  }
  
  if (terminal.value) {
    // 直接清理终端，不需要重新加载插件
    terminal.value.dispose()
    terminal.value = null
  }
  
  fitAddon.value = null
  webLinksAddon.value = null
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