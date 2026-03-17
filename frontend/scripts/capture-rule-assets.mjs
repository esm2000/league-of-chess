#!/usr/bin/env node

import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import http from 'node:http';
import net from 'node:net';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { spawn, spawnSync } from 'node:child_process';

const FRONTEND_DIR = path.resolve(process.cwd());
const PROJECT_ROOT = path.resolve(FRONTEND_DIR, '..');
const BUILD_DIR = path.join(FRONTEND_DIR, 'build');
const DEFAULT_OUTPUT_DIR = path.join(FRONTEND_DIR, 'src', 'assets', 'rules', 'generated');
const PYTHON_GIF_SCRIPT = path.join(FRONTEND_DIR, 'scripts', 'build_rule_gif.py');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

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
            if (error) {
                reject(error);
                return;
            }
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
        if (code === 0) {
            resolve();
            return;
        }

        reject(new Error(`${command} ${args.join(' ')} exited with code ${code}.`));
    });
});

const stopProcess = (childProcess) => new Promise((resolve) => {
    if (!childProcess) {
        resolve();
        return;
    }

    if (childProcess.exitCode !== null) {
        resolve();
        return;
    }

    let settled = false;

    const finish = () => {
        if (settled) {
            return;
        }

        settled = true;
        resolve();
    };

    childProcess.once('exit', finish);
    childProcess.kill('SIGTERM');

    setTimeout(() => {
        if (childProcess.exitCode === null) {
            childProcess.kill('SIGKILL');
        }
    }, 5000);
});

const waitForHttpOk = async (url, timeoutMs) => {
    const deadline = Date.now() + timeoutMs;

    while (Date.now() < deadline) {
        try {
            const response = await fetch(url);
            if (response.ok) {
                return;
            }
        } catch (error) {
            // Retry until timeout.
        }

        await sleep(200);
    }

    throw new Error(`Timed out waiting for ${url}.`);
};

const startStaticServer = async (port) => {
    const serverProcess = spawn(findPythonExecutable(), ['-m', 'http.server', String(port), '--bind', '127.0.0.1'], {
        cwd: BUILD_DIR,
        stdio: 'ignore'
    });

    await waitForHttpOk(`http://127.0.0.1:${port}`, 15000);

    return serverProcess;
};

const CANDIDATE_BROWSER_PATHS = [
    process.env.CHROME_EXECUTABLE_PATH,
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
].filter(Boolean);

const findBrowserExecutable = () => {
    for (const candidatePath of CANDIDATE_BROWSER_PATHS) {
        if (existsSync(candidatePath)) {
            return candidatePath;
        }
    }

    throw new Error('No supported Chromium-based browser was found. Set CHROME_EXECUTABLE_PATH to a local Chrome/Edge/Chromium binary.');
};

const CANDIDATE_PYTHON_PATHS = [
    process.env.PYTHON_EXECUTABLE,
    process.env.VIRTUAL_ENV ? path.join(process.env.VIRTUAL_ENV, 'bin', 'python3') : null,
    path.join(PROJECT_ROOT, 'env', 'bin', 'python3'),
    'python3',
    'python'
].filter(Boolean);

const pythonHasPillow = (pythonExecutable) => {
    const result = spawnSync(pythonExecutable, ['-c', 'import PIL'], {
        stdio: 'ignore'
    });

    return result.status === 0;
};

const findPythonExecutable = () => {
    for (const candidatePath of CANDIDATE_PYTHON_PATHS) {
        if (candidatePath.includes(path.sep) && !existsSync(candidatePath)) {
            continue;
        }

        if (pythonHasPillow(candidatePath)) {
            return candidatePath;
        }
    }

    throw new Error('No Python executable with Pillow available was found. Set PYTHON_EXECUTABLE to a Python binary that can import PIL.');
};

const waitForJson = async (url, timeoutMs) => {
    const deadline = Date.now() + timeoutMs;

    while (Date.now() < deadline) {
        try {
            const response = await fetch(url);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            // Retry until timeout.
        }

        await sleep(200);
    }

    throw new Error(`Timed out waiting for ${url}.`);
};

const startBrowser = async (debugPort, baseUrl) => {
    const userDataDir = await mkdtemp(path.join(os.tmpdir(), 'league-of-chess-browser-'));
    const browserProcess = spawn(findBrowserExecutable(), [
        '--headless=new',
        '--disable-gpu',
        '--hide-scrollbars',
        '--mute-audio',
        '--no-first-run',
        '--no-default-browser-check',
        `--remote-debugging-port=${debugPort}`,
        `--user-data-dir=${userDataDir}`,
        'about:blank'
    ], {
        stdio: 'ignore'
    });

    await waitForJson(`http://127.0.0.1:${debugPort}/json/list`, 15000);

    return { browserProcess, userDataDir, baseUrl };
};

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

            if (!payload.id) {
                return;
            }

            const pendingMessage = this.pendingMessages.get(payload.id);
            if (!pendingMessage) {
                return;
            }

            this.pendingMessages.delete(payload.id);

            if (payload.error) {
                pendingMessage.reject(new Error(payload.error.message));
                return;
            }

            pendingMessage.resolve(payload.result);
        });
    }

    async ready() {
        await this.openPromise;
    }

    async send(method, params = {}) {
        await this.ready();

        const id = ++this.nextMessageId;
        const message = JSON.stringify({ id, method, params });

        const responsePromise = new Promise((resolve, reject) => {
            this.pendingMessages.set(id, { resolve, reject });
        });

        this.socket.send(message);

        return responsePromise;
    }

    async close() {
        if (this.socket.readyState === WebSocket.OPEN) {
            this.socket.close();
        }
    }
}

const getPageWebSocketUrl = async (debugPort) => {
    const targets = await waitForJson(`http://127.0.0.1:${debugPort}/json/list`, 10000);
    const pageTarget = targets.find((target) => target.type === 'page');

    if (!pageTarget?.webSocketDebuggerUrl) {
        throw new Error('No debuggable page target was found.');
    }

    return pageTarget.webSocketDebuggerUrl;
};

const evaluateJson = async (session, expression) => {
    const result = await session.send('Runtime.evaluate', {
        expression,
        returnByValue: true,
        awaitPromise: true
    });

    return result.result?.value;
};

const navigate = async (session, url) => {
    await session.send('Page.navigate', { url });
};

const waitForValue = async (session, expression, timeoutMs) => {
    const deadline = Date.now() + timeoutMs;

    while (Date.now() < deadline) {
        try {
            const value = await evaluateJson(session, expression);

            if (value) {
                return value;
            }
        } catch (error) {
            // Retry while the page context is reloading.
        }

        await sleep(150);
    }

    throw new Error(`Timed out waiting for browser expression: ${expression}`);
};

const capturePng = async (session, outputPath, clip) => {
    const screenshot = await session.send('Page.captureScreenshot', {
        format: 'png',
        clip: {
            ...clip,
            scale: 1
        }
    });

    await writeFile(outputPath, Buffer.from(screenshot.data, 'base64'));
};

const applyEdgeOffset = (clipRect, edgeOffset = {}) => {
    if (!clipRect) {
        return null;
    }

    const offset = edgeOffset || {};
    const nextLeft = clipRect.x + (offset.left || 0);
    const nextTop = clipRect.y + (offset.top || 0);
    const nextRight = clipRect.x + clipRect.width + (offset.right || 0);
    const nextBottom = clipRect.y + clipRect.height + (offset.bottom || 0);

    return {
        x: Math.max(0, Math.round(nextLeft)),
        y: Math.max(0, Math.round(nextTop)),
        width: Math.max(1, Math.round(nextRight - nextLeft)),
        height: Math.max(1, Math.round(nextBottom - nextTop))
    };
};

const toClipRect = (bounds, padding = 0) => {
    const left = Math.max(0, Math.floor(bounds.left - padding));
    const top = Math.max(0, Math.floor(bounds.top - padding));
    const right = Math.ceil(bounds.right + padding);
    const bottom = Math.ceil(bounds.bottom + padding);

    return {
        x: left,
        y: top,
        width: Math.max(1, right - left),
        height: Math.max(1, bottom - top)
    };
};

const getModelBounds = (boxModel) => {
    const border = boxModel.model.border;
    const xs = [border[0], border[2], border[4], border[6]];
    const ys = [border[1], border[3], border[5], border[7]];

    return {
        left: Math.min(...xs),
        top: Math.min(...ys),
        right: Math.max(...xs),
        bottom: Math.max(...ys)
    };
};

const getDocumentNodeId = async (session) => {
    const { root } = await session.send('DOM.getDocument', { depth: 0 });
    return root.nodeId;
};

const querySelectorNodeId = async (session, selector) => {
    const documentNodeId = await getDocumentNodeId(session);
    const result = await session.send('DOM.querySelector', {
        nodeId: documentNodeId,
        selector
    });

    return result.nodeId || null;
};

const getSelectorBounds = async (session, selector) => {
    const nodeId = await querySelectorNodeId(session, selector);

    if (!nodeId) {
        return null;
    }

    const boxModel = await session.send('DOM.getBoxModel', { nodeId });
    return getModelBounds(boxModel);
};

const waitForSceneReady = async (session, sceneId, stepIndex) => waitForValue(
    session,
    `(() => {
        const params = new URLSearchParams(window.location.search);
        if (document.readyState !== 'complete') {
            return false;
        }

        if (params.get('captureScene') !== '${sceneId}') {
            return false;
        }

        if (Number.parseInt(params.get('captureStep') || '0', 10) !== ${stepIndex}) {
            return false;
        }

        return !Array.from(document.images).some((image) => !image.complete);
    })()`,
    20000
);

const resolveClipFromPage = async (session, sceneId, stepIndex, crop) => {
    const cropJson = JSON.stringify(crop);

    const clipJson = await waitForValue(
        session,
        `(() => {
            const params = new URLSearchParams(window.location.search);
            if (document.readyState !== 'complete') {
                return null;
            }

            if (params.get('captureScene') !== '${sceneId}') {
                return null;
            }

            if (Number.parseInt(params.get('captureStep') || '0', 10) !== ${stepIndex}) {
                return null;
            }

            if (Array.from(document.images).some((image) => !image.complete)) {
                return null;
            }

            const crop = ${cropJson};

            const toClipRect = (rect, padding = 0) => {
                const left = Math.max(0, Math.floor(rect.left - padding));
                const top = Math.max(0, Math.floor(rect.top - padding));
                const right = Math.ceil(rect.right + padding);
                const bottom = Math.ceil(rect.bottom + padding);

                return {
                    x: left,
                    y: top,
                    width: Math.max(1, right - left),
                    height: Math.max(1, bottom - top)
                };
            };

            const applyEdgeOffset = (clipRect, edgeOffset = {}) => {
                if (!clipRect) {
                    return null;
                }

                const offset = edgeOffset || {};
                const nextLeft = clipRect.x + (offset.left || 0);
                const nextTop = clipRect.y + (offset.top || 0);
                const nextRight = clipRect.x + clipRect.width + (offset.right || 0);
                const nextBottom = clipRect.y + clipRect.height + (offset.bottom || 0);

                return {
                    x: Math.max(0, Math.round(nextLeft)),
                    y: Math.max(0, Math.round(nextTop)),
                    width: Math.max(1, Math.round(nextRight - nextLeft)),
                    height: Math.max(1, Math.round(nextBottom - nextTop))
                };
            };

            const getSquareElement = ([row, col]) => document.querySelector('[data-square="' + row + '-' + col + '"]');

            if (crop.type === 'inner-board') {
                const boardGrid = document.querySelector('[data-board-grid="true"]');
                return boardGrid
                    ? JSON.stringify(applyEdgeOffset(toClipRect(boardGrid.getBoundingClientRect(), crop.padding || 0), crop.edgeOffset))
                    : null;
            }

            if (crop.type === 'board-frame') {
                const boardFrame = document.querySelector('[data-board-frame="true"]');
                return boardFrame
                    ? JSON.stringify(applyEdgeOffset(toClipRect(boardFrame.getBoundingClientRect(), crop.padding || 0), crop.edgeOffset))
                    : null;
            }

            if (crop.type === 'squares') {
                const startSquare = getSquareElement(crop.from);
                const endSquare = getSquareElement(crop.to);

                if (!startSquare || !endSquare) {
                    return null;
                }

                const startRect = startSquare.getBoundingClientRect();
                const endRect = endSquare.getBoundingClientRect();
                return JSON.stringify(applyEdgeOffset(
                    toClipRect({
                        left: Math.min(startRect.left, endRect.left),
                        top: Math.min(startRect.top, endRect.top),
                        right: Math.max(startRect.right, endRect.right),
                        bottom: Math.max(startRect.bottom, endRect.bottom)
                    }, crop.padding || 0),
                    crop.edgeOffset
                ));
            }

            return null;
        })()`,
        20000
    );

    return JSON.parse(clipJson);
};

const parseCliArgs = (argv) => {
    const parsedArgs = {
        outputDir: DEFAULT_OUTPUT_DIR,
        sceneFilter: null,
        skipBuild: false,
        keepFrames: false
    };

    for (let index = 0; index < argv.length; index += 1) {
        const arg = argv[index];

        if (arg === '--output-dir') {
            parsedArgs.outputDir = path.resolve(FRONTEND_DIR, argv[index + 1]);
            index += 1;
            continue;
        }

        if (arg === '--scene') {
            parsedArgs.sceneFilter = argv[index + 1].split(',').filter(Boolean);
            index += 1;
            continue;
        }

        if (arg === '--skip-build') {
            parsedArgs.skipBuild = true;
            continue;
        }

        if (arg === '--keep-frames') {
            parsedArgs.keepFrames = true;
        }
    }

    return parsedArgs;
};

const getManifest = async (session, baseUrl) => {
    await navigate(session, `${baseUrl}/?captureMode=1`);
    return waitForValue(
        session,
        `(() => {
            const params = new URLSearchParams(window.location.search);
            return params.get('captureMode') === '1'
                && !params.has('captureScene')
                && window.__RULE_CAPTURE_SCENES__
                && window.__RULE_CAPTURE_SCENES__.length
                ? window.__RULE_CAPTURE_SCENES__
                : null;
        })()`,
        20000
    );
};

const ensureBuildExists = async (skipBuild) => {
    if (skipBuild) {
        if (!existsSync(BUILD_DIR)) {
            throw new Error('Cannot use --skip-build because frontend/build does not exist.');
        }
        return;
    }

    await runCommand('npm', ['run', 'build-local-dev']);
};

const renderGif = async (outputPath, frameDelayMs, framePaths) => {
    await runCommand(findPythonExecutable(), [PYTHON_GIF_SCRIPT, outputPath, String(frameDelayMs), ...framePaths]);
};

const captureScene = async (session, baseUrl, scene, outputDir, framesDir) => {
    const framePaths = [];

    for (let stepIndex = 0; stepIndex < scene.stepCount; stepIndex += 1) {
        const sceneUrl = `${baseUrl}/?captureMode=1&captureScene=${scene.id}&captureStep=${stepIndex}`;
        await navigate(session, sceneUrl);

        try {
            await waitForSceneReady(session, scene.id, stepIndex);
            const clip = await resolveClipFromPage(session, scene.id, stepIndex, scene.crop);

            if (!clip) {
                throw new Error('Unable to resolve a clip rectangle from the rendered DOM.');
            }

            const frameOutputPath = path.join(framesDir, `${scene.id}-${String(stepIndex).padStart(2, '0')}.png`);
            await capturePng(session, frameOutputPath, clip);
            framePaths.push(frameOutputPath);
        } catch (error) {
            const debugState = await evaluateJson(session, `(() => ({
                startRect: (() => {
                    const element = document.querySelector('[data-square="${scene.crop?.from?.[0] ?? 'x'}-${scene.crop?.from?.[1] ?? 'y'}"]');
                    if (!element) {
                        return null;
                    }
                    const rect = element.getBoundingClientRect();
                    return [rect.left, rect.top, rect.right, rect.bottom];
                })(),
                endRect: (() => {
                    const element = document.querySelector('[data-square="${scene.crop?.to?.[0] ?? 'x'}-${scene.crop?.to?.[1] ?? 'y'}"]');
                    if (!element) {
                        return null;
                    }
                    const rect = element.getBoundingClientRect();
                    return [rect.left, rect.top, rect.right, rect.bottom];
                })(),
                href: window.location.href,
                readyState: document.readyState,
                captureReady: window.__RULE_CAPTURE_READY__ || false,
                captureError: window.__RULE_CAPTURE_ERROR__ || null,
                capture: window.__RULE_CAPTURE__ || null,
                squareCount: document.querySelectorAll('[data-square]').length,
                boardFramePresent: Boolean(document.querySelector('[data-board-frame="true"]')),
                boardGridPresent: Boolean(document.querySelector('[data-board-grid="true"]')),
                imageCount: document.images.length,
                bodyText: document.body.innerText.slice(0, 500)
            }))()`);
            throw new Error(`${error.message}\nBrowser debug: ${JSON.stringify(debugState, null, 2)}`);
        }
    }

    const outputPath = path.join(outputDir, scene.outputFile);
    await mkdir(path.dirname(outputPath), { recursive: true });

    if (scene.format === 'png') {
        await writeFile(outputPath, await readFile(framePaths[0]));
        return outputPath;
    }

    await renderGif(outputPath, scene.frameDelayMs, framePaths);
    return outputPath;
};

const main = async () => {
    const args = parseCliArgs(process.argv.slice(2));
    const serverPort = await getAvailablePort();
    const debugPort = await getAvailablePort();
    const baseUrl = `http://127.0.0.1:${serverPort}`;

    let serverProcess;
    let browserProcess;
    let browserUserDataDir;
    let frameTempDir;

    try {
        await ensureBuildExists(args.skipBuild);
        await mkdir(args.outputDir, { recursive: true });

        serverProcess = await startStaticServer(serverPort);

        const browser = await startBrowser(debugPort, baseUrl);
        browserProcess = browser.browserProcess;
        browserUserDataDir = browser.userDataDir;

        const session = new CdpSession(await getPageWebSocketUrl(debugPort));
        await session.send('Page.enable');
        await session.send('Runtime.enable');
        await session.send('DOM.enable');
        await session.send('Emulation.setDeviceMetricsOverride', {
            width: 1600,
            height: 1400,
            deviceScaleFactor: 2,
            mobile: false
        });

        const manifest = await getManifest(session, baseUrl);
        const sceneList = args.sceneFilter
            ? manifest.filter((scene) => args.sceneFilter.includes(scene.id))
            : manifest;

        if (!sceneList.length) {
            throw new Error('No capture scenes matched the requested filter.');
        }

        frameTempDir = await mkdtemp(path.join(os.tmpdir(), 'league-of-chess-rule-frames-'));

        for (const scene of sceneList) {
            const outputPath = await captureScene(session, baseUrl, scene, args.outputDir, frameTempDir);
            process.stdout.write(`Captured ${scene.id} -> ${outputPath}\n`);
        }

        await session.close();
    } finally {
        await stopProcess(serverProcess);
        await stopProcess(browserProcess);

        if (frameTempDir && !args.keepFrames) {
            await rm(frameTempDir, { recursive: true, force: true });
        }

        if (browserUserDataDir) {
            await rm(browserUserDataDir, { recursive: true, force: true });
        }
    }
};

main().catch((error) => {
    process.stderr.write(`${error.stack || error.message}\n`);
    process.exitCode = 1;
});
