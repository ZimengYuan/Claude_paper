globalThis.__timing__.logStart('Load chunks/routes/api/index.get2');import { d as defineEventHandler, a as getQuery, c as createError } from '../../nitro/nitro.mjs';
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

const index_get = defineEventHandler(async (event) => {
  const query = getQuery(event);
  try {
    return await callScholarBridge("list_papers", {
      query: typeof query.q === "string" ? query.q : "",
      project: typeof query.project === "string" ? query.project : "",
      show_all: query.showAll === "true"
    });
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || "Failed to load papers"
    });
  }
});

export { index_get as default };;globalThis.__timing__.logEnd('Load chunks/routes/api/index.get2');
//# sourceMappingURL=index.get2.mjs.map
