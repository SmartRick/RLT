export const statusTextMap = {
  'NEW': '新建',
  'SUBMITTED': '已提交',
  'MARKING': '标记中',
  'MARKED': '已标记',
  'TRAINING': '训练中',
  'COMPLETED': '已完成',
  'ERROR': '错误'
}

export const getStatusText = (status) => {
  return statusTextMap[status] || status || '未知状态'
} 