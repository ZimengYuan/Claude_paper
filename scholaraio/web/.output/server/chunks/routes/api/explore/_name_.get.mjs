globalThis.__timing__.logStart('Load chunks/routes/api/explore/_name_.get');import { d as defineEventHandler, g as getRouterParam, c as createError } from '../../../nitro/nitro.mjs';
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

const _name__get = defineEventHandler(async (event) => {
  const name = getRouterParam(event, "name");
  try {
    return await callScholarBridge("get_explore", {
      name: decodeURIComponent(name || "")
    });
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || "Failed to load library analysis"
    });
  }
});

export { _name__get as default };;globalThis.__timing__.logEnd('Load chunks/routes/api/explore/_name_.get');
//# sourceMappingURL=_name_.get.mjs.map
