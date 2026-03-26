import { callScholarBridge } from '../../utils/python.js'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)

  try {
    return await callScholarBridge('list_papers', {
      query: typeof query.q === 'string' ? query.q : '',
      project: typeof query.project === 'string' ? query.project : '',
      show_all: query.showAll === 'true'
    })
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || 'Failed to load papers'
    })
  }
})
