globalThis.__timing__.logStart('Load chunks/routes/api/papers/_id_.get');import { d as defineEventHandler, g as getRouterParam, c as createError } from '../../../nitro/nitro.mjs';
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

const _id__get = defineEventHandler(async (event) => {
  const id = getRouterParam(event, "id");
  try {
    return await callScholarBridge("get_paper", {
      paper_ref: decodeURIComponent(id || "")
    });
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || "Failed to load paper"
    });
  }
});

export { _id__get as default };;globalThis.__timing__.logEnd('Load chunks/routes/api/papers/_id_.get');
//# sourceMappingURL=_id_.get.mjs.map
