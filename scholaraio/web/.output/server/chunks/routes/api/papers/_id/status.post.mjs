globalThis.__timing__.logStart('Load chunks/routes/api/papers/_id/status.post');import { d as defineEventHandler, g as getRouterParam, r as readBody, c as createError } from '../../../../nitro/nitro.mjs';
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

const status_post = defineEventHandler(async (event) => {
  const id = getRouterParam(event, "id");
  const body = await readBody(event);
  try {
    return await callScholarBridge("set_read_status", {
      paper_ref: decodeURIComponent(id || ""),
      status: body.status
    });
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || "Failed to update read status"
    });
  }
});

export { status_post as default };;globalThis.__timing__.logEnd('Load chunks/routes/api/papers/_id/status.post');
//# sourceMappingURL=status.post.mjs.map
