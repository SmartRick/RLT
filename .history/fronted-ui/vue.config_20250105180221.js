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
  },
  configureWebpack: {
    resolve: {
      fallback: {
        "url": require.resolve("url/"),
        "http": require.resolve("stream-http"),
        "https": require.resolve("https-browserify"),
        "stream": require.resolve("stream-browserify"),
        "assert": require.resolve("assert/"),
        "util": require.resolve("util/"),
        "buffer": require.resolve("buffer/"),
        "crypto": require.resolve("crypto-browserify")
      }
    }
  }
})
