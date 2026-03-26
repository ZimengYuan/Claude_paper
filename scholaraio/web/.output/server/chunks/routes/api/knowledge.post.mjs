globalThis.__timing__.logStart('Load chunks/routes/api/knowledge.post');import { d as defineEventHandler, r as readBody, c as createError } from '../../nitro/nitro.mjs';
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

const knowledge_post = defineEventHandler(async (event) => {
  const body = await readBody(event);
  try {
    return await callScholarBridge("append_knowledge", {
      note: body.note,
      category: body.category || "general"
    });
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || "Failed to add note"
    });
  }
});

export { knowledge_post as default };;globalThis.__timing__.logEnd('Load chunks/routes/api/knowledge.post');
//# sourceMappingURL=knowledge.post.mjs.map
