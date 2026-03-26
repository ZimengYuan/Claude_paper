globalThis.__timing__.logStart('Load chunks/routes/api/graph.get');import { d as defineEventHandler, a as getQuery, c as createError } from '../../nitro/nitro.mjs';
import { c as callScholarBridge } from '../../_/python.mjs';
import 'node:http';
import 'node:https';
import 'node:events';
import 'node:buffer';
import 'node:fs';
import 'node:path';
import 'node:crypto';
import 'node:url';
import 'child_process';
import 'fs';
import 'path';
import 'url';

function parseIntParam(value, fallback) {
  const parsed = Number.parseInt(String(value == null ? "" : value), 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}
const graph_get = defineEventHandler(async (event) => {
  try {
    const query = getQuery(event);
    return await callScholarBridge("get_graph", {
      mode: typeof query.mode === "string" ? query.mode : "citation",
      scope: typeof query.scope === "string" ? query.scope : "library",
      project: typeof query.project === "string" ? query.project : "",
      paper_ref: typeof query.paper_ref === "string" ? query.paper_ref : "",
      min_shared: parseIntParam(query.min_shared, 2),
      max_nodes: parseIntParam(query.max_nodes, 80)
    });
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || "Failed to load graph"
    });
  }
});

export { graph_get as default };;globalThis.__timing__.logEnd('Load chunks/routes/api/graph.get');
//# sourceMappingURL=graph.get.mjs.map
