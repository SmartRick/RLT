const { defineConfig } = require('@vue/cli-service')
const webpack = require('webpack')

module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        pathRewrite: {
          '^/api': '/api'
        },
        ws: true
      }
    }
  },
  configureWebpack: {
    resolve: {
      fallback: {
        "url": false,
        "http": false,
        "https": false,
        "zlib": false,
        "stream": false,
        "util": false,
        "buffer": false,
        "crypto": false,
        "process": false,
        "assert": false
      }
    },
    plugins: [
      new webpack.ProvidePlugin({
        process: 'process/browser',
      })
    ]
  }
})
