import { callScholarBridge } from '../../../utils/python.js'

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  const body = await readBody(event)

  try {
    return await callScholarBridge('enqueue_generate', {
      paper_ref: decodeURIComponent(id || ''),
      types: Array.isArray(body.types) ? body.types : ['summary', 'rating']
    })
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || 'Failed to start generation'
    })
  }
})
