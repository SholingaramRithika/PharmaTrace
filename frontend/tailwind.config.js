const v = (n) => `rgb(var(--${n}) / <alpha-value>)`
export default { content: ['./index.html', './src/**/*.{ts,tsx}'], theme: { extend: {
  colors: { bg: v('bg'), card: v('card'), panel: v('panel'), ink: v('ink'), mute: v('mute'), line: v('line'), accent: v('accent'), coral: v('coral') },
  fontFamily: { head: ['Orbitron','sans-serif'], body: ['Inter','system-ui','sans-serif'], mono: ['JetBrains Mono','monospace'] } } } }
