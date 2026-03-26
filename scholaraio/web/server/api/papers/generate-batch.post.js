import { callScholarBridge } from '../../utils/python.js'

export default defineEventHandler(async (event) => {
  const body = await readBody(event)

  try {
    return await callScholarBridge('enqueue_generate_batch', {
      paper_ids: Array.isArray(body.paper_ids) ? body.paper_ids : [],
      types: Array.isArray(body.types) ? body.types : ['summary', 'rating']
    })
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || 'Failed to start batch generation'
    })
  }
})
