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
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
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

onMounted(() => {
  initTerminal()
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
    }
  })

  // 添加插件
  const fitAddon = new FitAddon()
  terminal.value.loadAddon(fitAddon)
  terminal.value.loadAddon(new WebLinksAddon())

  // 打开终端
  terminal.value.open(terminalRef.value)
  fitAddon.fit()

  // 连接WebSocket
  connectWebSocket()

  // 监听窗口大小变化
  window.addEventListener('resize', () => fitAddon.fit())
}

const connectWebSocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/api/terminal/${props.asset.id}`
  
  socket.value = new WebSocket(wsUrl)
  
  socket.value.onopen = () => {
    terminal.value.writeln('Connected to terminal...')
  }
  
  socket.value.onmessage = (event) => {
    terminal.value.write(event.data)
  }
  
  socket.value.onclose = () => {
    terminal.value.writeln('\r\nConnection closed.')
  }
  
  // 发送终端输入到服务器
  terminal.value.onData(data => {
    if (socket.value && socket.value.readyState === WebSocket.OPEN) {
      socket.value.send(data)
    }
  })
}

const cleanupTerminal = () => {
  if (socket.value) {
    socket.value.close()
  }
  if (terminal.value) {
    terminal.value.dispose()
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
}
</style> 