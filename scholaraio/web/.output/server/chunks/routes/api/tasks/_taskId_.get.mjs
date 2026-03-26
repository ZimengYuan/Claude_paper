globalThis.__timing__.logStart('Load chunks/routes/api/tasks/_taskId_.get');import { d as defineEventHandler, g as getRouterParam, c as createError } from '../../../nitro/nitro.mjs';
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

const _taskId__get = defineEventHandler(async (event) => {
  const taskId = getRouterParam(event, "taskId");
  try {
    return await callScholarBridge("get_task", {
      task_id: taskId
    });
  } catch (error) {
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || "Failed to load task"
    });
  }
});

export { _taskId__get as default };;globalThis.__timing__.logEnd('Load chunks/routes/api/tasks/_taskId_.get');
//# sourceMappingURL=_taskId_.get.mjs.map
