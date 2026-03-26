import { callScholarBridge } from '../../utils/python.js'

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')

  try {
    return await callScholarBridge('get_paper', {
      paper_ref: decodeURIComponent(id || '')
    })
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || 'Failed to load paper'
    })
  }
})
