import { callScholarBridge } from '../utils/python.js'

export default defineEventHandler(async (event) => {
  const body = await readBody(event)

  try {
    return await callScholarBridge('append_knowledge', {
      note: body.note,
      category: body.category || 'general'
    })
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || 'Failed to add note'
    })
  }
})
