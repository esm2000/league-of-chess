#!/usr/bin/env node

/**
 * Capture a replay GIF for a game by rendering each replay state in headless
 * Chrome and screenshotting the board.
 *
 * Requires:
 *   - The backend running on localhost:8080 (or --api-url)
 *   - A game ID with replay history (at least 2 turns played)
 *   - Chrome/Edge/Chromium installed
 *   - Python with Pillow (for GIF assembly)
 *
 * Usage:
 *   node scripts/capture-replay-gif.mjs --game-id <id> [--output <path>] [--skip-build] [--api-url <url>]
 */

import { mkdtemp, mkdir, rm, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import net from 'node:net';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { spawn, spawnSync } from 'node:child_process';

const FRONTEND_DIR = path.resolve(process.cwd());
const PROJECT_ROOT = path.resolve(FRONTEND_DIR, '..');
const BUILD_DIR = path.join(FRONTEND_DIR, 'build');
const PYTHON_GIF_SCRIPT = path.join(FRONTEND_DIR, 'scripts', 'build_rule_gif.py');
const DEFAULT_OUTPUT_DIR = path.join(PROJECT_ROOT, 'replays');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// ---------------------------------------------------------------------------
// Shared utilities (adapted from capture-rule-assets.mjs)
// ---------------------------------------------------------------------------

const getAvailablePort = () => new Promise((resolve, reject) => {
    const server = net.createServer();
    server.on('error', reject);
    server.listen(0, '127.0.0.1', () => {
        const address = server.address();
        if (!address || typeof address === 'string') {
            reject(new Error('Unable to determine an available port.'));
            return;
        }
        const { port } = address;
        server.close((error) => {
            if (error) { reject(error); return; }
            resolve(port);
        });
    });
});

const runCommand = (command, args, options = {}) => new Promise((resolve, reject) => {
    const child = spawn(command, args, {
        cwd: options.cwd || FRONTEND_DIR,
        env: { ...process.env, ...(options.env || {}) },
        stdio: options.stdio || 'inherit'
    });
    child.on('error', reject);
    child.on('close', (code) => {
        if (code === 0) { resolve(); return; }
        reject(new Error(`${command} ${args.join(' ')} exited with code ${code}.`));
    });
});

const stopProcess = (childProcess) => new Promise((resolve) => {
    if (!childProcess || childProcess.exitCode !== null) { resolve(); return; }
    let settled = false;
    const finish = () => { if (!settled) { settled = true; resolve(); } };
    childProcess.once('exit', finish);
    childProcess.kill('SIGTERM');
    setTimeout(() => { if (childProcess.exitCode === null) childProcess.kill('SIGKILL'); }, 5000);
});

const waitForHttpOk = async (url, timeoutMs) => {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
        try { const r = await fetch(url); if (r.ok) return; } catch {}
        await sleep(200);
    }
    throw new Error(`Timed out waiting for ${url}.`);
};

const waitForJson = async (url, timeoutMs) => {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
        try { const r = await fetch(url); if (r.ok) return await r.json(); } catch {}
        await sleep(200);
    }
    throw new Error(`Timed out waiting for ${url}.`);
};

const CANDIDATE_BROWSER_PATHS = [
    process.env.CHROME_EXECUTABLE_PATH,
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',
    '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable',
    '/usr/bin/chromium-browser', '/usr/bin/chromium', '/snap/bin/chromium'
].filter(Boolean);

const findBrowserExecutable = () => {
    for (const p of CANDIDATE_BROWSER_PATHS) { if (existsSync(p)) return p; }
    throw new Error('No supported Chromium-based browser found. Set CHROME_EXECUTABLE_PATH.');
};

const CANDIDATE_PYTHON_PATHS = [
    process.env.PYTHON_EXECUTABLE,
    process.env.VIRTUAL_ENV ? path.join(process.env.VIRTUAL_ENV, 'bin', 'python3') : null,
    path.join(PROJECT_ROOT, 'env', 'bin', 'python3'),
    'python3', 'python'
].filter(Boolean);

const findAnyPython = () => {
    for (const p of ['python3', 'python', ...CANDIDATE_PYTHON_PATHS]) {
        if (p.includes(path.sep) && !existsSync(p)) continue;
        if (spawnSync(p, ['--version'], { stdio: 'ignore' }).status === 0) return p;
    }
    throw new Error('No Python executable found.');
};

const findPythonWithPillow = () => {
    for (const p of CANDIDATE_PYTHON_PATHS) {
        if (p.includes(path.sep) && !existsSync(p)) continue;
        if (spawnSync(p, ['-c', 'import PIL'], { stdio: 'ignore' }).status === 0) return p;
    }
    throw new Error('No Python with Pillow found. Set PYTHON_EXECUTABLE.');
};

// ---------------------------------------------------------------------------
// CDP Session
// ---------------------------------------------------------------------------

class CdpSession {
    constructor(webSocketUrl) {
        this.webSocketUrl = webSocketUrl;
        this.nextMessageId = 0;
        this.pendingMessages = new Map();
        this.socket = new WebSocket(webSocketUrl);
        this.openPromise = new Promise((resolve, reject) => {
            this.socket.addEventListener('open', () => resolve());
            this.socket.addEventListener('error', reject);
        });
        this.socket.addEventListener('message', (event) => {
            const payload = JSON.parse(event.data.toString());
            if (!payload.id) return;
            const pending = this.pendingMessages.get(payload.id);
            if (!pending) return;
            this.pendingMessages.delete(payload.id);
            if (payload.error) { pending.reject(new Error(payload.error.message)); return; }
            pending.resolve(payload.result);
        });
    }
    async ready() { await this.openPromise; }
    async send(method, params = {}) {
        await this.ready();
        const id = ++this.nextMessageId;
        const responsePromise = new Promise((resolve, reject) => {
            this.pendingMessages.set(id, { resolve, reject });
        });
        this.socket.send(JSON.stringify({ id, method, params }));
        return responsePromise;
    }
    async close() { if (this.socket.readyState === WebSocket.OPEN) this.socket.close(); }
}

// ---------------------------------------------------------------------------
// Browser helpers
// ---------------------------------------------------------------------------

const startStaticServer = async (port) => {
    const serverProcess = spawn(findAnyPython(), ['-m', 'http.server', String(port), '--bind', '127.0.0.1'], {
        cwd: BUILD_DIR, stdio: 'ignore'
    });
    await waitForHttpOk(`http://127.0.0.1:${port}`, 15000);
    return serverProcess;
};

const startBrowser = async (debugPort) => {
    const userDataDir = await mkdtemp(path.join(os.tmpdir(), 'replay-gif-browser-'));
    const browserProcess = spawn(findBrowserExecutable(), [
        '--headless=new', '--disable-gpu', '--hide-scrollbars', '--mute-audio',
        '--no-first-run', '--no-default-browser-check',
        `--remote-debugging-port=${debugPort}`, `--user-data-dir=${userDataDir}`,
        'about:blank'
    ], { stdio: 'ignore' });
    await waitForJson(`http://127.0.0.1:${debugPort}/json/list`, 15000);
    return { browserProcess, userDataDir };
};

const getPageWebSocketUrl = async (debugPort) => {
    const targets = await waitForJson(`http://127.0.0.1:${debugPort}/json/list`, 10000);
    const page = targets.find((t) => t.type === 'page');
    if (!page?.webSocketDebuggerUrl) throw new Error('No debuggable page target found.');
    return page.webSocketDebuggerUrl;
};

const evaluateJson = async (session, expression) => {
    const result = await session.send('Runtime.evaluate', {
        expression, returnByValue: true, awaitPromise: true
    });
    return result.result?.value;
};

const navigate = async (session, url) => { await session.send('Page.navigate', { url }); };

const waitForValue = async (session, expression, timeoutMs) => {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
        try { const v = await evaluateJson(session, expression); if (v) return v; } catch {}
        await sleep(150);
    }
    throw new Error(`Timed out waiting for: ${expression}`);
};

const capturePng = async (session, outputPath, clip) => {
    const screenshot = await session.send('Page.captureScreenshot', {
        format: 'png', clip: { ...clip, scale: 1 }
    });
    await writeFile(outputPath, Buffer.from(screenshot.data, 'base64'));
};

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

const parseArgs = (argv) => {
    const args = { gameId: null, output: null, skipBuild: false, keepFrames: false, apiUrl: 'http://localhost:8080' };
    for (let i = 0; i < argv.length; i++) {
        if (argv[i] === '--game-id') { args.gameId = argv[++i]; continue; }
        if (argv[i] === '--output') { args.output = path.resolve(argv[++i]); continue; }
        if (argv[i] === '--api-url') { args.apiUrl = argv[++i]; continue; }
        if (argv[i] === '--skip-build') { args.skipBuild = true; continue; }
        if (argv[i] === '--keep-frames') { args.keepFrames = true; continue; }
    }
    if (!args.gameId) throw new Error('Usage: capture-replay-gif.mjs --game-id <id> [--output <path>] [--skip-build]');
    if (!args.output) args.output = path.join(DEFAULT_OUTPUT_DIR, `replay_${args.gameId}.gif`);
    return args;
};

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

const main = async () => {
    const args = parseArgs(process.argv.slice(2));

    // Verify the replay endpoint has data
    process.stdout.write(`Fetching replay states for game ${args.gameId}...\n`);
    const replayStates = await waitForJson(`${args.apiUrl}/api/game/${args.gameId}/replay`, 10000);
    if (!replayStates.length) throw new Error(`No replay states found for game ${args.gameId}.`);
    process.stdout.write(`Found ${replayStates.length} replay states.\n`);

    // Build frontend if needed
    if (!args.skipBuild) {
        process.stdout.write('Building frontend...\n');
        await runCommand('npm', ['run', 'build-local-dev']);
    } else if (!existsSync(BUILD_DIR)) {
        throw new Error('Cannot use --skip-build because frontend/build does not exist.');
    }

    const serverPort = await getAvailablePort();
    const debugPort = await getAvailablePort();
    const baseUrl = `http://127.0.0.1:${serverPort}`;

    let serverProcess, browserProcess, browserUserDataDir, frameTempDir;

    try {
        serverProcess = await startStaticServer(serverPort);

        const browser = await startBrowser(debugPort);
        browserProcess = browser.browserProcess;
        browserUserDataDir = browser.userDataDir;

        const session = new CdpSession(await getPageWebSocketUrl(debugPort));
        await session.send('Page.enable');
        await session.send('Runtime.enable');
        await session.send('DOM.enable');
        await session.send('Emulation.setDeviceMetricsOverride', {
            width: 1600, height: 1400, deviceScaleFactor: 2, mobile: false
        });

        frameTempDir = await mkdtemp(path.join(os.tmpdir(), 'replay-gif-frames-'));
        const framePaths = [];
        const pythonExecutable = findPythonWithPillow();

        // Inject replay data into each page load to avoid CORS issues
        const replayDataJson = JSON.stringify(replayStates);
        await session.send('Page.addScriptToEvaluateOnNewDocument', {
            source: `window.__REPLAY_DATA__ = ${replayDataJson};`
        });

        for (let step = 0; step < replayStates.length; step++) {
            const url = `${baseUrl}/?captureMode=1&captureReplay=${args.gameId}&captureStep=${step}`;
            await navigate(session, url);

            const clipJson = await waitForValue(
                session,
                `(() => {
                    if (window.__RULE_CAPTURE_READY__ && window.__RULE_CAPTURE__?.clip) {
                        return JSON.stringify(window.__RULE_CAPTURE__.clip);
                    }
                    return null;
                })()`,
                20000
            );

            const clip = JSON.parse(clipJson);
            const framePath = path.join(frameTempDir, `frame-${String(step).padStart(3, '0')}.png`);
            await capturePng(session, framePath, clip);
            framePaths.push(framePath);
            process.stdout.write(`  Captured step ${step + 1}/${replayStates.length}\n`);
        }

        // Assemble GIF
        await mkdir(path.dirname(args.output), { recursive: true });
        await runCommand(pythonExecutable, [PYTHON_GIF_SCRIPT, args.output, '1250', ...framePaths]);
        process.stdout.write(`\nReplay GIF saved to ${args.output}\n`);

        await session.close();
    } finally {
        await stopProcess(serverProcess);
        await stopProcess(browserProcess);
        if (frameTempDir && !args.keepFrames) await rm(frameTempDir, { recursive: true, force: true });
        if (browserUserDataDir) await rm(browserUserDataDir, { recursive: true, force: true });
    }
};

main().catch((error) => {
    process.stderr.write(`${error.stack || error.message}\n`);
    process.exitCode = 1;
});
