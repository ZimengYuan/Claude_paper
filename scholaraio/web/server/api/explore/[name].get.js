import { callScholarBridge } from '../../utils/python.js'

export default defineEventHandler(async (event) => {
  const name = getRouterParam(event, 'name')

  try {
    return await callScholarBridge('get_explore', {
      name: decodeURIComponent(name || '')
    })
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || 'Failed to load library analysis'
    })
  }
})
