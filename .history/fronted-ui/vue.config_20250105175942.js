const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',  // 后端服务地址
        changeOrigin: true,
        pathRewrite: {
          '^/api': '/api'  // 不重写路径
        },
        ws: true  // 启用 websocket 代理
      }
    }
  }
})
