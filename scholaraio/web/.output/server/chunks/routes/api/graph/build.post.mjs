globalThis.__timing__.logStart('Load chunks/routes/api/graph/build.post');import { d as defineEventHandler, r as readBody, c as createError } from '../../../nitro/nitro.mjs';
import { c as callScholarBridge } from '../../../_/python.mjs';
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
const build_post = defineEventHandler(async (event) => {
  try {
    const body = await readBody(event);
    return await callScholarBridge("build_graph", {
      mode: body && typeof body.mode === "string" ? body.mode : "citation",
      scope: body && typeof body.scope === "string" ? body.scope : "library",
      project: body && typeof body.project === "string" ? body.project : "",
      paper_ref: body && typeof body.paper_ref === "string" ? body.paper_ref : "",
      min_shared: parseIntParam(body && body.min_shared, 2),
      max_nodes: parseIntParam(body && body.max_nodes, 80)
    });
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || "Failed to build graph"
    });
  }
});

export { build_post as default };;globalThis.__timing__.logEnd('Load chunks/routes/api/graph/build.post');
//# sourceMappingURL=build.post.mjs.map
