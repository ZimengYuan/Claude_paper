globalThis.__timing__.logStart('Load chunks/routes/api/knowledge.get');import { d as defineEventHandler, c as createError } from '../../nitro/nitro.mjs';
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

const knowledge_get = defineEventHandler(async () => {
  try {
    return await callScholarBridge("get_knowledge");
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || "Failed to load knowledge"
    });
  }
});

export { knowledge_get as default };;globalThis.__timing__.logEnd('Load chunks/routes/api/knowledge.get');
//# sourceMappingURL=knowledge.get.mjs.map
