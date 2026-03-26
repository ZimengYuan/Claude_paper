import { spawn } from 'child_process'
import { existsSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const currentDir = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.resolve(currentDir, '../../../../')

function pathIfExists(candidate) {
  if (!candidate) return ''
  return existsSync(candidate) ? candidate : ''
}

function resolveCondaPython(prefix) {
  if (!prefix) return ''
  return pathIfExists(path.join(prefix, 'bin', 'python3')) || pathIfExists(path.join(prefix, 'bin', 'python'))
}

function resolveBridgePython() {
  const explicit = process.env.SCHOLARAIO_PYTHON || process.env.SCHOLARAIO_BRIDGE_PYTHON
  if (explicit) return explicit

  const currentEnvName = process.env.CONDA_DEFAULT_ENV || path.basename(process.env.CONDA_PREFIX || '')
  if (currentEnvName && !/^node\d+$/i.test(currentEnvName)) {
    const currentEnvPython = resolveCondaPython(process.env.CONDA_PREFIX)
    if (currentEnvPython) return currentEnvPython
  }

  const home = process.env.HOME || ''
  const fallbackCandidates = [
    path.join(home, 'miniconda3', 'envs', 'scholaraio', 'bin', 'python'),
    path.join(home, 'miniconda3', 'bin', 'python3')
  ]
  for (const candidate of fallbackCandidates) {
    const resolved = pathIfExists(candidate)
    if (resolved) return resolved
  }

  return 'python3'
}

const bridgePython = resolveBridgePython()

function buildBridgeEnv() {
  return {
    ...process.env,
    PYTHONUTF8: '1',
    SCHOLARAIO_PYTHON: bridgePython
  }
}

function parseBridgeError(stderr, fallbackMessage) {
  const text = (stderr || '').trim()
  if (!text) {
    return { statusCode: 500, message: fallbackMessage }
  }
  try {
    const parsed = JSON.parse(text)
    return {
      statusCode: parsed.status_code || 500,
      message: parsed.message || fallbackMessage
    }
  } catch {
    return { statusCode: 500, message: text || fallbackMessage }
  }
}

export async function callScholarBridge(action, payload = {}) {
  return await new Promise((resolve, reject) => {
    const proc = spawn(bridgePython, ['-m', 'scholaraio.web_bridge', action], {
      cwd: repoRoot,
      env: buildBridgeEnv()
    })

    let stdout = ''
    let stderr = ''

    proc.stdout.on('data', (data) => {
      stdout += data.toString()
    })
    proc.stderr.on('data', (data) => {
      stderr += data.toString()
    })
    proc.on('error', (error) => {
      reject({ statusCode: 500, message: error.message })
    })
    proc.on('close', (code) => {
      if (code !== 0) {
        reject(parseBridgeError(stderr, `Bridge action failed: ${action}`))
        return
      }
      try {
        resolve(stdout.trim() ? JSON.parse(stdout) : null)
      } catch {
        reject({ statusCode: 500, message: `Invalid JSON from bridge: ${stdout}` })
      }
    })

    proc.stdin.end(JSON.stringify(payload))
  })
}
