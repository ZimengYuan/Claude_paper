import { callScholarBridge } from '../../utils/python.js'

function parseIntParam(value, fallback) {
  const parsed = Number.parseInt(String(value == null ? '' : value), 10)
  return Number.isFinite(parsed) ? parsed : fallback
}

export default defineEventHandler(async (event) => {
  try {
    const body = await readBody(event)
    return await callScholarBridge('build_graph', {
      mode: body && typeof body.mode === 'string' ? body.mode : 'citation',
      scope: body && typeof body.scope === 'string' ? body.scope : 'library',
      project: body && typeof body.project === 'string' ? body.project : '',
      paper_ref: body && typeof body.paper_ref === 'string' ? body.paper_ref : '',
      min_shared: parseIntParam(body && body.min_shared, 2),
      max_nodes: parseIntParam(body && body.max_nodes, 80)
    })
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || 'Failed to build graph'
    })
  }
})
