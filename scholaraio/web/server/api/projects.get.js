import { callScholarBridge } from '../utils/python.js'

export default defineEventHandler(async () => {
  try {
    return await callScholarBridge('list_projects')
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || 'Failed to load projects'
    })
  }
})
