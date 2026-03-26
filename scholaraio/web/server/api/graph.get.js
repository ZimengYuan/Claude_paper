import { callScholarBridge } from '../utils/python.js'

function parseIntParam(value, fallback) {
  const parsed = Number.parseInt(String(value == null ? '' : value), 10)
  return Number.isFinite(parsed) ? parsed : fallback
}

export default defineEventHandler(async (event) => {
  try {
    const query = getQuery(event)
    return await callScholarBridge('get_graph', {
      mode: typeof query.mode === 'string' ? query.mode : 'citation',
      scope: typeof query.scope === 'string' ? query.scope : 'library',
      project: typeof query.project === 'string' ? query.project : '',
      paper_ref: typeof query.paper_ref === 'string' ? query.paper_ref : '',
      min_shared: parseIntParam(query.min_shared, 2),
      max_nodes: parseIntParam(query.max_nodes, 80)
    })
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || 'Failed to load graph'
    })
  }
})
