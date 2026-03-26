globalThis.__timing__.logStart('Load chunks/routes/api/papers/generate-batch.post');import { d as defineEventHandler, r as readBody, c as createError } from '../../../nitro/nitro.mjs';
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

const generateBatch_post = defineEventHandler(async (event) => {
  const body = await readBody(event);
  try {
    return await callScholarBridge("enqueue_generate_batch", {
      paper_ids: Array.isArray(body.paper_ids) ? body.paper_ids : [],
      types: Array.isArray(body.types) ? body.types : ["summary", "rating"]
    });
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || "Failed to start batch generation"
    });
  }
});

export { generateBatch_post as default };;globalThis.__timing__.logEnd('Load chunks/routes/api/papers/generate-batch.post');
//# sourceMappingURL=generate-batch.post.mjs.map
