
import { TegakiEngine, createBundle } from 'tegaki'
import caveat from 'tegaki/fonts/caveat'

const stage = document.querySelector<HTMLDivElement>('#stage')!
const status = document.querySelector<HTMLParagraphElement>('#status')!
const seek = document.querySelector<HTMLInputElement>('#seek')!
const clock = document.querySelector<HTMLSpanElement>('#clock')!

const text = [
  'Handwriting test',
  '√x + ∫θ dx = π',
  '± × ÷ → ∞ ≠ ≤ ≥',
  '∑ ∠ ∴'
].join('\n')

const customGlyphs = { ...caveat.glyphData }

// First genuine custom mathematical glyph: square root.
customGlyphs['√'] = {
  w: 850,
  t: 0.65,
  s: [
    {
      // Short descending check, then rise.
      p: [
        [40, -180, 48],
        [100, -120, 50],
        [165, -20, 54],
        [230, -300, 58]
      ],
      d: 0,
      a: 0.22
    },
    {
      // Tall radical stem.
      p: [
        [230, -300, 58],
        [340, -520, 55],
        [450, -690, 52],
        [560, -720, 50]
      ],
      d: 0.22,
      a: 0.22
    },
    {
      // Extended horizontal overbar.
      p: [
        [560, -720, 50],
        [900, -720, 48],
        [1300, -720, 46]
      ],
      d: 0.44,
      a: 0.21
    }
  ]
}

// Temporary placeholders for the remaining symbols.
// These are NOT final mathematical glyphs.
for (const symbol of [
  '∫', 'θ', 'π', '±', '×', '÷', '→',
  '∞', '≠', '≤', '≥', '∑', '∠', '∴'
]) {
  customGlyphs[symbol] = caveat.glyphData['S']
}

const testBundle = createBundle({
  family: 'TutorMe-Caveat-Test',
  fullFamily: caveat.fullFamily,
  fontUrl: caveat.fontUrl,
  fullFontUrl: caveat.fullFontUrl,
  glyphData: customGlyphs,
  lineCap: caveat.lineCap,
  unitsPerEm: caveat.unitsPerEm,
  ascender: caveat.ascender,
  descender: caveat.descender
})

let engine: TegakiEngine | null = null

function updateClock() {
  if (!engine) return

  const duration = engine.duration
  const current = engine.currentTime

  seek.max = String(Math.max(duration, 0.01))
  seek.value = String(Math.min(current, duration))

  clock.textContent =
    `${current.toFixed(2)} / ${duration.toFixed(2)} s`

  requestAnimationFrame(updateClock)
}

try {
  engine = new TegakiEngine(stage, {
    text,
    font: testBundle,
    shaper: false,
    seed: 42,

    timing: {
      glyphGap: 0.12,
      wordGap: 0.2,
      lineGap: 0.35
    },

    onChangeTimeline: (timeline) => {
      status.textContent =
        `Timeline ready: ${timeline.entries.length} entries, ` +
        `${timeline.totalDuration.toFixed(2)} seconds`
    },

    onComplete: () => {
      status.textContent = 'Playback complete.'
    }
  })

  document.querySelector('#play')!.addEventListener('click', () => {
    engine?.play()
  })

  document.querySelector('#pause')!.addEventListener('click', () => {
    engine?.pause()
  })

  document.querySelector('#restart')!.addEventListener('click', () => {
    engine?.restart()
  })

  document.querySelector('#skip')!.addEventListener('click', () => {
    engine?.seek('100%')
  })

  seek.addEventListener('input', () => {
    engine?.pause()
    engine?.seek(Number(seek.value))
  })

  status.textContent = 'Tegaki engine created.'

  updateClock()
  engine.play()

} catch (error) {
  console.error('Tegaki test failed:', error)
  status.textContent = `ERROR: ${String(error)}`
}
