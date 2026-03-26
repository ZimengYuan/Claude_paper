globalThis.__timing__.logStart('Load chunks/routes/api/explore/_name/roadmap.post');import { d as defineEventHandler, g as getRouterParam, r as readBody, c as createError } from '../../../../nitro/nitro.mjs';
import { c as callScholarBridge } from '../../../../_/python.mjs';
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

const roadmap_post = defineEventHandler(async (event) => {
  const name = getRouterParam(event, "name");
  const body = await readBody(event);
  try {
    return await callScholarBridge("generate_explore_roadmap", {
      name: decodeURIComponent(name || ""),
      force: !!(body == null ? void 0 : body.force)
    });
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || "Failed to generate library roadmap"
    });
  }
});

export { roadmap_post as default };;globalThis.__timing__.logEnd('Load chunks/routes/api/explore/_name/roadmap.post');
//# sourceMappingURL=roadmap.post.mjs.map
