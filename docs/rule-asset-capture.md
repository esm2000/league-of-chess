# Rule Asset Capture

Rule asset capture workflow for regenerating rule screenshots and GIFs from deterministic board scenes instead of manual browser captures.

## How It Works

- Scene definitions live in `frontend/src/capture/ruleScenes.js`
- Capture mode is enabled with `?captureMode=1`
- A specific scene is rendered with `?captureScene=<scene-id>&captureStep=<n>`
- Crop regions are defined in board coordinates, so assets can target the full board, the inner board only, or a subsection of squares
- The capture script builds the frontend, serves the static build locally, drives a headless Chromium browser, and saves cropped outputs

## Commands

```bash
cd frontend
npm run capture:rules
```

By default, outputs are written to `frontend/src/assets/rules/`.

Useful flags:

```bash
# Capture one or more scenes
npm run capture:rules -- --scene knight_movement,queen_stun

# Overwrite the main rules asset folder directly
npm run capture:rules -- --output-dir src/assets/rules

# Reuse an existing frontend/build directory
npm run capture:rules -- --skip-build

# Keep intermediate PNG frames for GIF scenes
npm run capture:rules -- --keep-frames
```

## Previewing Scenes

Build or start the frontend, then open:

```text
http://localhost:3000/?captureMode=1
```

That index page lists the available scene ids and lets you preview them one at a time.
