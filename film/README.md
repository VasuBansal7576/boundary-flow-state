# Boundary video

This is the editable source for the four-minute video. It includes the composition, narration, music, real footage cuts, and trace screenshots. The finished MP4 and full original recording are in [Releases](https://github.com/VasuBansal7576/boundary-flow-state/releases/tag/flow-state-2026).

## Render the supplied edit

Install Node.js and FFmpeg, then run:

```sh
cd film
npm ci
npm run check
npm run render -- --output renders/boundary-hackathon-master.mp4 --quality high --workers 4 --video-frame-format png
python3 finish_hackathon.py
```

The final file is `renders/boundary-flow-state-4min.mp4`: 1920×1080, 30 fps, four minutes. Rendering uses the included media and runs locally. No model calls or paid renderer are required.

## Edit or inspect

- `index.html` and `compositions/`: animation and scene timing.
- `SCRIPT.md`: narration.
- `STORYBOARD.md`: scene plan, including the earlier 90-second cut.
- `assets/`: narration, music, font, and GSAP.
- `capture/`: original footage cuts and native interface screenshots.
- `proof/`: source references, capture timing, render checks, and audio measurements.

The film combines footage recorded during the real run with labeled trace and console screenshots captured afterward. The 17 October MCP check is separate from the 16 October swarm run.

The capture and generation scripts preserve the original production workflow and its directory assumptions. You do not need to run them to render this supplied edit.
