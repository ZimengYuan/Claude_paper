import { callScholarBridge } from '../../utils/python.js'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)

  try {
    return await callScholarBridge('search_knowledge', {
      query: typeof query.q === 'string' ? query.q : ''
    })
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || 'Failed to search knowledge'
    })
  }
})
