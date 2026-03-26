import { callScholarBridge } from '../../../utils/python.js'

export default defineEventHandler(async (event) => {
  const name = getRouterParam(event, 'name')
  const body = await readBody(event)

  try {
    return await callScholarBridge('generate_explore_roadmap', {
      name: decodeURIComponent(name || ''),
      force: !!body?.force
    })
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || 'Failed to generate library roadmap'
    })
  }
})
