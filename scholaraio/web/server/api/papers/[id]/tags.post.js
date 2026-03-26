import { callScholarBridge } from '../../../utils/python.js'

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  const body = await readBody(event)

  try {
    return await callScholarBridge('set_tags', {
      paper_ref: decodeURIComponent(id || ''),
      tags: Array.isArray(body.tags) ? body.tags : []
    })
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || 'Failed to update tags'
    })
  }
})
