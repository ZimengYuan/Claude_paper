import { callScholarBridge } from '../../utils/python.js'

export default defineEventHandler(async (event) => {
  const body = await readBody(event)

  try {
    return await callScholarBridge('append_paper_summary', {
      title: body.title || body.paperId || '',
      summary: body.summary,
      category: body.category || 'paper-summary'
    })
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || 'Failed to add paper summary to knowledge base'
    })
  }
})
