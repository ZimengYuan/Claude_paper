globalThis.__timing__.logStart('Load chunks/routes/api/tags.get');import { d as defineEventHandler, c as createError } from '../../nitro/nitro.mjs';
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

const tags_get = defineEventHandler(async () => {
  try {
    return await callScholarBridge("list_tags");
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || "Failed to load tags"
    });
  }
});

export { tags_get as default };;globalThis.__timing__.logEnd('Load chunks/routes/api/tags.get');
//# sourceMappingURL=tags.get.mjs.map
