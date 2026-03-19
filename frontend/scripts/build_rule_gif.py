from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image


def main() -> int:
    if len(sys.argv) < 4:
        print("Usage: build_rule_gif.py <output_path> <frame_delay_ms> <frame_1> [frame_2 ...]", file=sys.stderr)
        return 1

    output_path = Path(sys.argv[1])
    frame_delay_ms = int(sys.argv[2])
    frame_paths = [Path(frame_path) for frame_path in sys.argv[3:]]

    frames = [Image.open(frame_path).convert("RGBA") for frame_path in frame_paths]
    palette_frames = [frame.convert("P", palette=Image.ADAPTIVE) for frame in frames]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    palette_frames[0].save(
        output_path,
        save_all=True,
        append_images=palette_frames[1:],
        duration=frame_delay_ms,
        loop=0,
        optimize=False,
        disposal=2,
    )

    for frame in frames:
        frame.close()

    for frame in palette_frames:
        frame.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
