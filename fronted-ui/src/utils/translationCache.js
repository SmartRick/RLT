import { ref } from 'vue'
import { commonApi } from '@/api/common'

// 创建全局翻译缓存，使用ref使其成为响应式对象
const translationCache = ref({})

/**
 * 从缓存获取翻译，如果不存在则从API获取并缓存
 * @param {string} text 要翻译的文本
 * @param {string} toLanguage 目标语言
 * @param {string} fromLanguage 源语言
 * @returns {Promise<{text: string, isLoading: boolean, isError: boolean}>} 翻译结果
 */
const getTranslation = async (text, toLanguage = 'zh', fromLanguage = 'en') => {
  if (!text) {
    return { text: '', isLoading: false, isError: false }
  }

  // 生成缓存键
  const cacheKey = `${text}:${fromLanguage}->${toLanguage}`
  
  // 检查缓存
  if (translationCache.value[cacheKey]) {
    return { 
      text: translationCache.value[cacheKey], 
      isLoading: false, 
      isError: false 
    }
  }
  
  // 从API获取翻译
  try {
    const result = await commonApi.translateText(text, toLanguage, fromLanguage)
    
    if (result && result.result) {
      // 缓存翻译结果
      translationCache.value[cacheKey] = result.result
      return { 
        text: result.result, 
        isLoading: false, 
        isError: false 
      }
    } else {
      return { 
        text: '翻译失败', 
        isLoading: false, 
        isError: true 
      }
    }
  } catch (error) {
    console.error('翻译失败:', error)
    return { 
      text: '翻译服务异常', 
      isLoading: false, 
      isError: true 
    }
  }
}

/**
 * 添加翻译到缓存
 * @param {string} text 原文本
 * @param {string} translation 翻译结果
 * @param {string} toLanguage 目标语言
 * @param {string} fromLanguage 源语言
 */
const addToCache = (text, translation, toLanguage = 'zh', fromLanguage = 'en') => {
  if (!text || !translation) return
  
  const cacheKey = `${text}:${fromLanguage}->${toLanguage}`
  translationCache.value[cacheKey] = translation
}

/**
 * 清除缓存
 */
const clearCache = () => {
  translationCache.value = {}
}

/**
 * 获取缓存大小
 * @returns {number} 缓存条目数量
 */
const getCacheSize = () => {
  return Object.keys(translationCache.value).length
}

export {
  translationCache,
  getTranslation,
  addToCache,
  clearCache,
  getCacheSize
} 