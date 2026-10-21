# Futuristic background layer

Visual-only enhancement. No routes, API calls, Neo4j queries, schema, or backend code were changed.

## What it is
`frontend/src/background/BackgroundScene.tsx` is mounted once in `Layout.tsx`, so it persists across every route and is not re-created on navigation.
Layers, back to front:

1. CSS gradients (midnight navy base, blue/cyan atmosphere, faint coral glow in corners)
2. Dotted "world" haze behind the hero
3. Four slow cyan/blue/coral light streaks (CSS, GPU-friendly)
4. SVG scientific motifs on the outer edges: molecules, DNA double helix, capsules
5. A single `<canvas>` with slow particles, pulsing glow nodes and fading proximity links

## Safety for the app
- Container is `position: fixed`, `pointer-events: none`, `aria-hidden`, `overflow: hidden` -> it cannot block graph drag/zoom, forms, scrolling or create horizontal overflow.
- Page content sits in a `relative z-10` wrapper above the scene.
- Graph nodes/edges are still drawn by Cytoscape from live Neo4j data; background particles are unrelated decoration.

## Performance
- Particle count scales with screen area (26 to 85), pixel ratio is capped at 1.5, glow uses layered circles (no `shadowBlur`).
- Animation pauses when the tab is hidden; resize is debounced; rAF, listeners and ResizeObserver are cleaned up on unmount.
- `prefers-reduced-motion: reduce` draws one static frame and disables CSS animation.

## Theming
All colours are CSS variables in `src/index.css` (`--scene-a`, `--glow-1`, `--motif`, ...). Dark mode is the full navy/cyan look; light mode uses a pale, low-contrast variant. The existing Light/Dark toggle is unchanged.

## Tuning
Edit `PALETTES` and the particle-count formula in `BackgroundScene.tsx`, or the variables in `index.css`.
