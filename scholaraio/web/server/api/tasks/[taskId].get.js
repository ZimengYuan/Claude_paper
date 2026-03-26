import { callScholarBridge } from '../../utils/python.js'

export default defineEventHandler(async (event) => {
  const taskId = getRouterParam(event, 'taskId')

  try {
    return await callScholarBridge('get_task', {
      task_id: taskId
    })
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || 'Failed to load task'
    })
  }
})
