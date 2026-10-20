import { memo, useEffect, useMemo, useRef } from 'react'
import { useTheme } from '../theme'

/**
 * Decorative, non-interactive background for the whole app.
 * Layers (back → front): CSS gradients, dotted "world" haze, light streaks,
 * SVG scientific motifs (molecules / DNA helix / capsules), canvas particle network.
 * It is mounted once in <Layout/>, so it persists across routes and never re-renders on navigation.
 * Everything is aria-hidden and pointer-events:none.
 */

type RGB = [number, number, number]
type Palette = { cores: RGB[]; line: RGB; lineAlpha: number; nodeAlpha: number }

const PALETTES: Record<'dark' | 'light', Palette> = {
  dark: { cores: [[90, 225, 255], [90, 225, 255], [70, 150, 255], [70, 150, 255], [255, 110, 90], [225, 95, 235]], line: [70, 190, 255], lineAlpha: 0.32, nodeAlpha: 1 },
  light: { cores: [[40, 120, 200], [20, 150, 190], [40, 120, 200], [200, 80, 70]], line: [50, 120, 190], lineAlpha: 0.16, nodeAlpha: 0.55 },
}

type P = { x: number; y: number; vx: number; vy: number; r: number; c: RGB; ph: number; sp: number }

function ParticleCanvas() {
  const ref = useRef<HTMLCanvasElement>(null)
  const { theme } = useTheme()
  const palette = useRef<Palette>(PALETTES[theme])
  palette.current = PALETTES[theme]
  const partsRef = useRef<P[]>([])

  useEffect(() => {
    const canvas = ref.current; if (!canvas) return
    const ctx = canvas.getContext('2d'); if (!ctx) return // e.g. jsdom
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    let reduced = mq.matches
    let w = 0, h = 0, dpr = 1, raf = 0, last = 0; const parts = partsRef.current

    const make = (): P => {
      const cores = palette.current.cores
      return { x: Math.random() * w, y: Math.random() * h, vx: (Math.random() - 0.5) * 0.18, vy: (Math.random() - 0.5) * 0.18,
        r: 0.8 + Math.random() * 1.8, c: cores[Math.floor(Math.random() * cores.length)], ph: Math.random() * Math.PI * 2, sp: 0.4 + Math.random() * 0.9 }
    }
    const resize = () => {
      const rect = canvas.getBoundingClientRect(); w = Math.max(1, rect.width); h = Math.max(1, rect.height)
      dpr = Math.min(window.devicePixelRatio || 1, 1.5)
      canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr); ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      const target = Math.round(Math.min(85, Math.max(26, (w * h) / 24000)))
      while (parts.length < target) parts.push(make())
      parts.length = target
      parts.forEach(p => { p.x = Math.min(p.x, w); p.y = Math.min(p.y, h) })
      draw(0)
    }
    const LINK = () => (w < 640 ? 95 : 135)

    function draw(t: number) {
      const pal = palette.current; ctx!.clearRect(0, 0, w, h)
      const link = LINK(), link2 = link * link
      for (let i = 0; i < parts.length; i++) {
        const a = parts[i]
        for (let j = i + 1; j < parts.length; j++) {
          const b = parts[j]; const dx = a.x - b.x, dy = a.y - b.y; const d2 = dx * dx + dy * dy
          if (d2 < link2) {
            const k = 1 - Math.sqrt(d2) / link
            ctx!.strokeStyle = `rgba(${pal.line[0]},${pal.line[1]},${pal.line[2]},${(k * pal.lineAlpha).toFixed(3)})`
            ctx!.lineWidth = 0.7; ctx!.beginPath(); ctx!.moveTo(a.x, a.y); ctx!.lineTo(b.x, b.y); ctx!.stroke()
          }
        }
      }
      for (const p of parts) {
        const pulse = 0.65 + 0.35 * Math.sin(t * 0.001 * p.sp + p.ph); const [r, g, b] = p.c; const al = pal.nodeAlpha * pulse
        ctx!.fillStyle = `rgba(${r},${g},${b},${(al * 0.10).toFixed(3)})`; ctx!.beginPath(); ctx!.arc(p.x, p.y, p.r * 5, 0, 6.283); ctx!.fill()
        ctx!.fillStyle = `rgba(${r},${g},${b},${(al * 0.22).toFixed(3)})`; ctx!.beginPath(); ctx!.arc(p.x, p.y, p.r * 2.4, 0, 6.283); ctx!.fill()
        ctx!.fillStyle = `rgba(${r},${g},${b},${Math.min(1, al).toFixed(3)})`; ctx!.beginPath(); ctx!.arc(p.x, p.y, p.r, 0, 6.283); ctx!.fill()
      }
    }
    const step = (t: number) => {
      raf = requestAnimationFrame(step)
      const dt = Math.min(48, t - last || 16); last = t
      const k = dt / 16
      for (const p of parts) {
        p.x += p.vx * k; p.y += p.vy * k
        if (p.x < -10) p.x = w + 10; else if (p.x > w + 10) p.x = -10
        if (p.y < -10) p.y = h + 10; else if (p.y > h + 10) p.y = -10
      }
      draw(t)
    }
    const start = () => { cancelAnimationFrame(raf); if (!reduced && !document.hidden) { last = 0; raf = requestAnimationFrame(step) } else draw(0) }
    const onVis = () => start()
    const onMotion = () => { reduced = mq.matches; start() }
    let rt = 0; const onResize = () => { window.clearTimeout(rt); rt = window.setTimeout(resize, 120) }

    resize(); start()
    window.addEventListener('resize', onResize); document.addEventListener('visibilitychange', onVis)
    mq.addEventListener?.('change', onMotion)
    const ro = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(onResize) : null; ro?.observe(canvas)
    return () => { cancelAnimationFrame(raf); window.clearTimeout(rt); window.removeEventListener('resize', onResize); document.removeEventListener('visibilitychange', onVis); mq.removeEventListener?.('change', onMotion); ro?.disconnect() }
  }, [])
  // recolour existing particles when the theme changes (no remount, no new animation loop)
  useEffect(() => { const cores = PALETTES[theme].cores; partsRef.current.forEach(p => { p.c = cores[Math.floor(Math.random() * cores.length)] }) }, [theme])
  return <canvas ref={ref} className="absolute inset-0 w-full h-full" />
}

/** Hexagonal ring molecule with two side chains. */
function Molecule({ x, y, r = 34, rot = 0, tails = 2 }: { x: number; y: number; r?: number; rot?: number; tails?: number }) {
  const pts = Array.from({ length: 6 }, (_, i) => { const a = (Math.PI / 3) * i + (rot * Math.PI) / 180; return [x + r * Math.cos(a), y + r * Math.sin(a)] as const })
  const out = Array.from({ length: tails }, (_, i) => { const idx = i * 2 + 1; const a = (Math.PI / 3) * idx + (rot * Math.PI) / 180; const [px, py] = pts[idx]
    return [px, py, px + r * 0.9 * Math.cos(a), py + r * 0.9 * Math.sin(a)] as const })
  return <g>
    <polygon points={pts.map(p => p.join(',')).join(' ')} fill="none" />
    {out.map(([x1, y1, x2, y2], i) => <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} />)}
    {pts.map(([px, py], i) => <circle key={i} cx={px} cy={py} r={i % 2 ? 3.2 : 2.2} className="bg-atom" fill="currentColor" stroke="none" style={{ animationDelay: `${i * 0.5}s` }} />)}
    {out.map(([, , x2, y2], i) => <circle key={i} cx={x2} cy={y2} r={4.2} fill="currentColor" stroke="none" opacity={0.9} />)}
  </g>
}


function Helix() {
  const { strands, rungs } = useMemo(() => {
    const H = 1000;
    const amp = 55;
    const cx = 100;
    const turns = 3.2;

    type Point = readonly [number, number];

    const pts = (phase: number): Point[] =>
      Array.from({ length: 101 }, (_, i) => {
        const y = (i / 100) * H;
        const x =
          cx +
          amp *
            Math.sin(
              (y / H) * turns * 2 * Math.PI + phase
            );

        return [x, y] as const;
      });

    const a = pts(0);
    const b = pts(Math.PI);

    const path = (points: readonly Point[]) =>
      points
        .map(
          ([x, y], i) =>
            `${i ? "L" : "M"}${x.toFixed(1)} ${y.toFixed(1)}`
        )
        .join(" ");

    const rungs: Array<readonly [Point, Point]> = [];

    for (let i = 0; i < 34; i++) {
      const k = 2 + i * 3;
      const p = a[k];
      const q = b[k];

      // Ignore invalid coordinates instead of crashing the page.
      if (!p || !q) continue;

      rungs.push([p, q]);
    }

    return {
      strands: [path(a), path(b)],
      rungs,
    };
  }, []);

  return (
    <g fill="none">
      {strands.map((d, i) => (
        <path key={i} d={d} strokeWidth={2.2} />
      ))}

      {rungs.map(([p, q], i) => (
        <g key={i}>
          <line
            x1={p[0]}
            y1={p[1]}
            x2={q[0]}
            y2={q[1]}
            strokeWidth={1}
            opacity={0.55}
          />

          <circle
            cx={p[0]}
            cy={p[1]}
            r={3}
            fill="currentColor"
            stroke="none"
            className="bg-atom"
            style={{ animationDelay: `${(i % 7) * 0.4}s` }}
          />

          <circle
            cx={q[0]}
            cy={q[1]}
            r={3}
            fill="currentColor"
            stroke="none"
            opacity={0.7}
          />
        </g>
      ))}
    </g>
  );
}


function Capsule({ x, y, rot, w = 150, h = 54 }: { x: number; y: number; rot: number; w?: number; h?: number }) {
  return <g transform={`translate(${x} ${y}) rotate(${rot})`} fill="none">
    <rect x={-w / 2} y={-h / 2} width={w} height={h} rx={h / 2} strokeWidth={1.6} />
    <line x1={0} y1={-h / 2} x2={0} y2={h / 2} strokeWidth={1.2} opacity={0.6} />
    <rect x={-w / 2 + 8} y={-h / 2 + 8} width={w * 0.38} height={9} rx={4.5} strokeWidth={1} opacity={0.45} />
  </g>
}

const STREAKS = [
  { top: '14%', left: '-10%', w: '46vw', rot: -8, d: '19s', delay: '0s', c: 'cyan' }, { top: '38%', left: '30%', w: '38vw', rot: 12, d: '26s', delay: '-8s', c: 'blue' },
  { top: '66%', left: '-6%', w: '52vw', rot: -4, d: '23s', delay: '-4s', c: 'cyan' }, { top: '82%', left: '40%', w: '40vw', rot: 7, d: '29s', delay: '-14s', c: 'coral' },
]

function BackgroundSceneImpl() {
  return <div className="bg-scene" aria-hidden="true" data-testid="bg-scene">
    <div className="bg-scene__base" />
    <div className="bg-scene__glow" />
    <div className="bg-scene__dots" />
    {STREAKS.map((s, i) => <i key={i} className={`bg-streak bg-streak--${s.c}`} style={{ top: s.top, left: s.left, width: s.w, transform: `rotate(${s.rot}deg)`, animationDuration: s.d, animationDelay: s.delay }} />)}
    {/* left edge: molecules + capsule */}
    <svg className="bg-motif bg-motif--left" viewBox="0 0 260 1000" preserveAspectRatio="xMinYMid slice" fill="none" strokeWidth="1.3">
      <Molecule x={90} y={150} r={38} rot={15} /><Molecule x={60} y={470} r={30} rot={40} tails={1} /><Molecule x={150} y={640} r={42} rot={-10} />
      <Capsule x={40} y={820} rot={-38} />
    </svg>
    {/* right edge: DNA helix + vial/capsule hints */}
    <svg className="bg-motif bg-motif--right" viewBox="0 0 200 1000" preserveAspectRatio="xMaxYMid slice" strokeWidth="1.3">
      <Helix />
    </svg>
    <svg className="bg-motif bg-motif--bottomright" viewBox="0 0 300 260" fill="none" strokeWidth="1.4">
      <Capsule x={190} y={170} rot={-28} w={190} h={64} /><Molecule x={70} y={90} r={30} rot={20} tails={1} />
    </svg>
    <div className="bg-scene__vignette" />
    <ParticleCanvas />
  </div>
}
const BackgroundScene = memo(BackgroundSceneImpl)
export default BackgroundScene
