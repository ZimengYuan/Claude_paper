import { callScholarBridge } from '../../../utils/python.js'

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  const body = await readBody(event)

  try {
    return await callScholarBridge('set_close_read', {
      paper_ref: decodeURIComponent(id || ''),
      enabled: typeof body.enabled === 'boolean' ? body.enabled : true
    })
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || 'Failed to update close-read state'
    })
  }
})
