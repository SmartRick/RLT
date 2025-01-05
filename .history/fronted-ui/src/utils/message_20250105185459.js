import { createVNode, render } from 'vue'
import Message from '@/components/common/Message.vue'

/**
 * @typedef {'success' | 'warning' | 'error' | 'info'} MessageType
 */

let messageInstance = null

/**
 * 创建消息实例
 * @param {Object} options 
 * @param {string} options.content - 消息内容
 * @param {MessageType} options.type - 消息类型
 * @param {number} options.duration - 显示时长
 */
const createMessage = (options) => {
  const container = document.createElement('div')
  
  const vnode = createVNode(Message, {
    content: options.content,
    type: options.type,
    duration: options.duration
  })
  
  render(vnode, container)
  document.body.appendChild(container)
  
  const instance = vnode.component
  instance.exposed.show()
  
  messageInstance = {
    vnode,
    container,
    close: () => {
      render(null, container)
      document.body.removeChild(container)
      messageInstance = null
    }
  }
  
  return messageInstance
}

/**
 * 消息提示服务
 */
const message = {
  /**
   * 显示成功消息
   * @param {string} content 消息内容
   * @param {number} [duration=3000] 显示时长
   */
  success(content, duration = 3000) {
    return createMessage({ content, type: 'success', duration })
  },

  /**
   * 显示警告消息
   * @param {string} content 消息内容
   * @param {number} [duration=3000] 显示时长
   */
  warning(content, duration = 3000) {
    return createMessage({ content, type: 'warning', duration })
  },

  /**
   * 显示错误消息
   * @param {string} content 消息内容
   * @param {number} [duration=3000] 显示时长
   */
  error(content, duration = 3000) {
    return createMessage({ content, type: 'error', duration })
  },

  /**
   * 显示信息消息
   * @param {string} content 消息内容
   * @param {number} [duration=3000] 显示时长
   */
  info(content, duration = 3000) {
    return createMessage({ content, type: 'info', duration })
  }
}

export default message 