import { callScholarBridge } from '../../../utils/python.js'

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')

  try {
    const markdown = await callScholarBridge('get_paper_markdown', {
      paper_ref: decodeURIComponent(id || '')
    })
    setHeader(event, 'content-type', 'text/plain; charset=utf-8')
    return markdown
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || 'Failed to load paper content'
    })
  }
})
