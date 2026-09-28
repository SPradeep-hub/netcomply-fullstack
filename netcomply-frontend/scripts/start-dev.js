import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const frontendDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const repoDir = path.resolve(frontendDir, '..')
const backendDir = path.join(repoDir, 'netcomply')
const python = process.env.PYTHON || findPython()
const children = []
let stopping = false

function findPython() {
  if (process.platform === 'win32') {
    const localAppData = process.env.LOCALAPPDATA || path.join(os.homedir(), 'AppData', 'Local')
    for (const version of ['Python313', 'Python312', 'Python311', 'Python310']) {
      const candidate = path.join(localAppData, 'Programs', 'Python', version, 'python.exe')
      if (existsSync(candidate)) return candidate
    }
    return 'py'
  }
  return 'python3'
}

function stop(exitCode = 0) {
  if (stopping) return
  stopping = true
  for (const child of children) {
    if (child.exitCode !== null) continue
    if (process.platform === 'win32' && child.pid) {
      spawn('taskkill', ['/pid', String(child.pid), '/t', '/f'], { stdio: 'ignore' })
    } else {
      child.kill('SIGTERM')
    }
  }
  process.exitCode = exitCode
}

function start(command, args, cwd, label) {
  const child = spawn(command, args, { cwd, stdio: 'inherit' })
  children.push(child)
  child.once('error', (error) => {
    console.error(`${label} could not start: ${error.message}`)
    if (label === 'Flask API') {
      console.error('Install Python and run: python -m pip install -r netcomply/requirements.txt')
    }
    stop(1)
  })
  child.once('exit', (code) => {
    if (!stopping) stop(code || 0)
  })
  return child
}

start(python, ['api.py'], backendDir, 'Flask API')
start(process.execPath, [path.join(frontendDir, 'node_modules', 'vite', 'bin', 'vite.js'), '--host', '127.0.0.1'], frontendDir, 'Vite')

console.log('NetComply is starting. Open http://127.0.0.1:5173 when Vite is ready.')
process.on('SIGINT', () => stop(0))
process.on('SIGTERM', () => stop(0))
