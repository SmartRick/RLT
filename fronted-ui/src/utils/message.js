import { createVNode, render } from 'vue'
import Message from '../components/common/Message.vue'

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
   * 成功提示
   * @param {string} content 提示内容
   * @param {number} duration 提示持续时间
   */
  success(content, duration = 3000) {
    return createMessage({
      type: 'success',
      content,
      duration
    })
  },
  
  /**
   * 错误提示
   * @param {string|Error|Object} error 错误信息或错误对象
   * @param {number} duration 提示持续时间
   */
  error(error, duration = 3000) {
    // 处理各种错误类型
    let content = '操作失败'
    
    if (typeof error === 'string') {
      content = error
    } else if (error instanceof Error) {
      content = error.message || '操作失败'
    } else if (error && error.msg) {
      // 处理统一格式的错误对象
      content = error.msg
    } else if (error && error.message) {
      content = error.message
    }
    
    return createMessage({
      type: 'error',
      content,
      duration
    })
  },
  
  /**
   * 警告提示
   * @param {string} content 提示内容
   * @param {number} duration 提示持续时间
   */
  warning(content, duration = 3000) {
    return createMessage({
      type: 'warning',
      content,
      duration
    })
  },
  
  /**
   * 信息提示
   * @param {string} content 提示内容
   * @param {number} duration 提示持续时间
   */
  info(content, duration = 3000) {
    return createMessage({
      type: 'info',
      content,
      duration
    })
  }
}

export default message 