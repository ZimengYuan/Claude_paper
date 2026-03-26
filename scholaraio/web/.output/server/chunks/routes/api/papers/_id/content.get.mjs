globalThis.__timing__.logStart('Load chunks/routes/api/papers/_id/content.get');import { d as defineEventHandler, g as getRouterParam, s as setHeader, c as createError } from '../../../../nitro/nitro.mjs';
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

const content_get = defineEventHandler(async (event) => {
  const id = getRouterParam(event, "id");
  try {
    const markdown = await callScholarBridge("get_paper_markdown", {
      paper_ref: decodeURIComponent(id || "")
    });
    setHeader(event, "content-type", "text/plain; charset=utf-8");
    return markdown;
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || "Failed to load paper content"
    });
  }
});

export { content_get as default };;globalThis.__timing__.logEnd('Load chunks/routes/api/papers/_id/content.get');
//# sourceMappingURL=content.get.mjs.map
