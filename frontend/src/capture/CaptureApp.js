import React, { useEffect, useState } from 'react';
import Board from '../components/Board';
import GameStateContext from '../context/GameStateContext';
import { getRuleScene, getRuleSceneManifest } from './ruleScenes';

const CAPTURE_MODE_PARAM = 'captureMode'
const CAPTURE_SCENE_PARAM = 'captureScene'
const CAPTURE_STEP_PARAM = 'captureStep'

const getCaptureSearchParams = () => new URLSearchParams(window.location.search)

const isCaptureModeEnabled = () => {
    const searchParams = getCaptureSearchParams()

    return searchParams.get(CAPTURE_MODE_PARAM) === '1' || searchParams.has(CAPTURE_SCENE_PARAM)
}

const clampStepIndex = (scene, rawStep) => {
    if (!scene) {
        return 0
    }

    const parsedStep = Number.parseInt(rawStep || '0', 10)

    if (Number.isNaN(parsedStep) || parsedStep < 0) {
        return 0
    }

    return Math.min(parsedStep, scene.steps.length - 1)
}

const toClipRect = (rect, padding = 0) => {
    const left = Math.max(0, Math.floor(rect.left - padding))
    const top = Math.max(0, Math.floor(rect.top - padding))
    const right = Math.ceil(rect.right + padding)
    const bottom = Math.ceil(rect.bottom + padding)

    return {
        x: left,
        y: top,
        width: Math.max(1, right - left),
        height: Math.max(1, bottom - top)
    }
}

const applyEdgeOffset = (clipRect, edgeOffset = {}) => {
    if (!clipRect) {
        return null
    }

    const nextLeft = clipRect.x + (edgeOffset.left || 0)
    const nextTop = clipRect.y + (edgeOffset.top || 0)
    const nextRight = clipRect.x + clipRect.width + (edgeOffset.right || 0)
    const nextBottom = clipRect.y + clipRect.height + (edgeOffset.bottom || 0)

    return {
        x: Math.max(0, Math.round(nextLeft)),
        y: Math.max(0, Math.round(nextTop)),
        width: Math.max(1, Math.round(nextRight - nextLeft)),
        height: Math.max(1, Math.round(nextBottom - nextTop))
    }
}

const getSquareElement = ([row, col]) => document.querySelector(`[data-square="${row}-${col}"]`)

const getCropRect = (crop) => {
    if (!crop) {
        return null
    }

    if (crop.type === 'inner-board') {
        const boardGrid = document.querySelector('[data-board-grid="true"]')

        if (!boardGrid) {
            return null
        }

        return applyEdgeOffset(
            toClipRect(boardGrid.getBoundingClientRect(), crop.padding || 0),
            crop.edgeOffset
        )
    }

    if (crop.type === 'board-frame') {
        const boardFrame = document.querySelector('[data-board-frame="true"]')

        if (!boardFrame) {
            return null
        }

        return applyEdgeOffset(
            toClipRect(boardFrame.getBoundingClientRect(), crop.padding || 0),
            crop.edgeOffset
        )
    }

    if (crop.type === 'squares') {
        const startSquare = getSquareElement(crop.from)
        const endSquare = getSquareElement(crop.to)

        if (!startSquare || !endSquare) {
            return null
        }

        const startRect = startSquare.getBoundingClientRect()
        const endRect = endSquare.getBoundingClientRect()
        const unionRect = {
            left: Math.min(startRect.left, endRect.left),
            top: Math.min(startRect.top, endRect.top),
            right: Math.max(startRect.right, endRect.right),
            bottom: Math.max(startRect.bottom, endRect.bottom)
        }

        return applyEdgeOffset(
            toClipRect(unionRect, crop.padding || 0),
            crop.edgeOffset
        )
    }

    return null
}

const publishCaptureMetadata = (scene, stepIndex, clipOverride = null) => {
    const clip = clipOverride || getCropRect(scene?.crop)

    window.__RULE_CAPTURE_SCENES__ = getRuleSceneManifest()
    window.__RULE_CAPTURE__ = scene ? {
        id: scene.id,
        format: scene.format,
        frameDelayMs: scene.frameDelayMs,
        stepCount: scene.steps.length,
        stepIndex,
        outputFile: `${scene.id}.${scene.format}`,
        crop: scene.crop,
        clip
    } : null
    window.__RULE_CAPTURE_READY__ = Boolean(scene && clip)
}

const CaptureMetadataBridge = ({ scene, stepIndex }) => {
    useEffect(() => {
        let cancelled = false

        window.__RULE_CAPTURE_READY__ = false
        window.__RULE_CAPTURE_ERROR__ = null
        window.__RULE_CAPTURE_SCENES__ = getRuleSceneManifest()

        const publishWhenReady = async () => {
            const fontReadyPromise = document.fonts?.ready || Promise.resolve()
            await fontReadyPromise

            const images = Array.from(document.images)
            await Promise.all(images.map((image) => (
                image.complete ? Promise.resolve() : new Promise((resolve) => {
                    image.addEventListener('load', resolve, { once: true })
                    image.addEventListener('error', resolve, { once: true })
                })
            )))

            let attempts = 0

            const publishOnStableLayout = () => {
                if (cancelled) {
                    return
                }

                const clip = getCropRect(scene?.crop)

                if (clip || attempts >= 60) {
                    publishCaptureMetadata(scene, stepIndex, clip)
                    return
                }

                attempts += 1
                requestAnimationFrame(publishOnStableLayout)
            }

            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    if (!cancelled) {
                        publishOnStableLayout()
                    }
                })
            })
        }

        publishWhenReady().catch((error) => {
            window.__RULE_CAPTURE_ERROR__ = error.message
        })

        return () => {
            cancelled = true
        }
    }, [scene, stepIndex])

    return null
}

const CaptureGameStateProvider = ({ initialState, children }) => {
    const [gameState, setGameState] = useState(initialState)

    useEffect(() => {
        setGameState(initialState)
    }, [initialState])

    const updateGameState = (nextGameState) => {
        setGameState((currentGameState) => ({
            ...nextGameState,
            updateGameState: currentGameState.updateGameState,
            restartGame: currentGameState.restartGame
        }))
    }

    const restartGame = () => {
        setGameState({
            ...initialState,
            updateGameState,
            restartGame
        })
    }

    return (
        <GameStateContext.Provider
            value={{
                ...gameState,
                updateGameState,
                restartGame
            }}
        >
            {children}
        </GameStateContext.Provider>
    )
}

const CaptureSceneIndex = () => {
    const sceneManifest = getRuleSceneManifest()

    useEffect(() => {
        publishCaptureMetadata(null, 0)
    }, [])

    return (
        <div style={{ fontFamily: 'Basic', padding: '1.5rem' }}>
            <h1>Rule Capture Scenes</h1>
            <p>Open a scene with <code>?captureScene=&lt;scene-id&gt;&amp;captureStep=0</code>.</p>
            <ul>
                {sceneManifest.map((scene) => (
                    <li key={scene.id}>
                        <a href={`/?captureMode=1&captureScene=${scene.id}&captureStep=0`}>
                            {scene.outputFile}
                        </a>
                        {' '}
                        ({scene.stepCount} step{scene.stepCount === 1 ? '' : 's'})
                    </li>
                ))}
            </ul>
        </div>
    )
}

const CaptureApp = () => {
    const searchParams = getCaptureSearchParams()
    const sceneId = searchParams.get(CAPTURE_SCENE_PARAM)
    const scene = getRuleScene(sceneId)
    const stepIndex = clampStepIndex(scene, searchParams.get(CAPTURE_STEP_PARAM))

    if (!scene) {
        return <CaptureSceneIndex />
    }

    return (
        <CaptureGameStateProvider initialState={scene.steps[stepIndex].state}>
            <div
                data-capture-shell="true"
                style={{
                    padding: '16px',
                    minHeight: '100vh',
                    boxSizing: 'border-box'
                }}
            >
                <Board />
            </div>
            <CaptureMetadataBridge scene={scene} stepIndex={stepIndex} />
        </CaptureGameStateProvider>
    )
}

export {
    CaptureApp,
    isCaptureModeEnabled
}
