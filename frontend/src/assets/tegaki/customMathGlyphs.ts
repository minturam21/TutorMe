type Point = [number, number];

type GlyphPath = {
  w: number;
  strokes: Point[][];
};

function line(points: Point[]): Point[] {
  return points;
}

function quadratic(
  start: Point,
  control: Point,
  end: Point,
  steps = 12
): Point[] {
  const result: Point[] = [];

  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const u = 1 - t;

    result.push([
      u * u * start[0] + 2 * u * t * control[0] + t * t * end[0],
      u * u * start[1] + 2 * u * t * control[1] + t * t * end[1],
    ]);
  }

  return result;
}

function dot(cx: number, cy: number, radius = 5): Point[] {
  return Array.from({ length: 9 }, (_, i) => {
    const angle = (i / 8) * Math.PI * 2;
    return [
      cx + Math.cos(angle) * radius,
      cy + Math.sin(angle) * radius,
    ];
  });
}

function makeGlyph(path: GlyphPath) {
  const strokeLengths = path.strokes.map((stroke) => {
    let length = 0;

    for (let i = 1; i < stroke.length; i++) {
      const dx = stroke[i][0] - stroke[i - 1][0];
      const dy = stroke[i][1] - stroke[i - 1][1];
      length += Math.hypot(dx, dy);
    }

    return length;
  });

  let clock = 0;

  const strokes = path.strokes.map((stroke, strokeIndex) => {
    const duration = Math.max(0.08, strokeLengths[strokeIndex] / 2600);
    const delay = clock;
    clock += duration + 0.035;

    return {
      d: delay,
      a: duration,
      p: stroke.map(([x, y]) => [x, y, 82]),
    };
  });

  return {
    w: path.w,
    t: Math.max(0.1, clock - 0.035),
    s: strokes,
  };
}

const glyphs: Record<string, GlyphPath> = {
  [String.fromCodePoint(0x2192)]: {
    w: 700,
    strokes: [line([[90, -300], [610, -300]]), line([[460, -440], [610, -300], [460, -160]])],
  },
  [String.fromCodePoint(0x2207)]: {
    w: 700,
    strokes: [line([[100, -470], [350, -100], [600, -470], [100, -470]])],
  },
  [String.fromCodePoint(0x2213)]: {
    w: 700,
    strokes: [
      line([[180, -410], [520, -410]]),
      line([[180, -170], [520, -170]]),
      line([[350, -260], [350, -80]]),
    ],
  },
  [String.fromCodePoint(0x2190)]: {
    w: 700,
    strokes: [line([[610, -300], [90, -300]]), line([[240, -440], [90, -300], [240, -160]])],
  },
  [String.fromCodePoint(0x2194)]: {
    w: 760,
    strokes: [
      line([[110, -300], [650, -300]]),
      line([[250, -440], [110, -300], [250, -160]]),
      line([[510, -440], [650, -300], [510, -160]]),
    ],
  },
  [String.fromCodePoint(0x21d2)]: {
    w: 760,
    strokes: [
      line([[90, -360], [500, -360]]),
      line([[90, -240], [500, -240]]),
      line([[390, -490], [650, -300], [390, -110]]),
    ],
  },
  [String.fromCodePoint(0x21d4)]: {
    w: 820,
    strokes: [
      line([[250, -360], [570, -360]]),
      line([[250, -240], [570, -240]]),

      // Left arrowhead
      line([[250, -360], [120, -300]]),
      line([[120, -300], [250, -240]]),

      // Right arrowhead
      line([[570, -360], [700, -300]]),
      line([[700, -300], [570, -240]]),
    ],
  },
  [String.fromCodePoint(0x2261)]: {
    w: 700,
    strokes: [
      line([[130, -410], [570, -410]]),
      line([[130, -300], [570, -300]]),
      line([[130, -190], [570, -190]]),
    ],
  },
  [String.fromCodePoint(0x222c)]: {
    w: 700,
    strokes: [
      [
        ...quadratic([280, -510], [170, -480], [230, -370], 12),
        ...quadratic([230, -370], [340, -250], [240, -130], 12).slice(1),
        ...quadratic([240, -130], [210, -60], [120, -80], 8).slice(1),
      ],
      [
        ...quadratic([490, -510], [380, -480], [440, -370], 12),
        ...quadratic([440, -370], [550, -250], [450, -130], 12).slice(1),
        ...quadratic([450, -130], [420, -60], [330, -80], 8).slice(1),
      ],
    ],
  },
  [String.fromCodePoint(0x222e)]: {
    w: 700,
    strokes: [
      [
        ...quadratic([350, -500], [150, -500], [150, -300], 12),
        ...quadratic([150, -300], [150, -100], [350, -100], 12).slice(1),
        ...quadratic([350, -100], [550, -100], [550, -300], 12).slice(1),
        ...quadratic([550, -300], [550, -500], [350, -500], 12).slice(1),
      ],
      line([[470, -520], [390, -390], [300, -250], [210, -100]]),
    ],
  },
  [String.fromCodePoint(0x221b)]: {
    w: 800,
    strokes: [
      line([[70, -250], [150, -250], [230, -80], [350, -500], [710, -500]]),
      line([[250, -500], [250, -430], [310, -430]]),
    ],
  },
  [String.fromCodePoint(0x221c)]: {
    w: 900,
    strokes: [
      line([[60, -250], [140, -250], [220, -80], [340, -500], [810, -500]]),
      line([[230, -500], [230, -430], [290, -430]]),
      line([[300, -500], [300, -430], [360, -430]]),
    ],
  },
  [String.fromCodePoint(0x221d)]: {
    w: 760,
    strokes: [
      quadratic([100, -300], [210, -120], [330, -300], 14),
      quadratic([330, -300], [450, -480], [570, -300], 14),
      quadratic([570, -300], [450, -120], [330, -300], 14),
      quadratic([330, -300], [210, -480], [100, -300], 14),
    ],
  },
  [String.fromCodePoint(0x2234)]: {
    w: 650,
    strokes: [dot(150, -150), dot(480, -150), dot(315, -430)],
  },
  [String.fromCodePoint(0x2235)]: {
    w: 650,
    strokes: [dot(150, -430), dot(480, -430), dot(315, -150)],
  },
  [String.fromCodePoint(0x2208)]: {
    w: 650,
    strokes: [
      quadratic([520, -430], [150, -540], [150, -300], 18),
      quadratic([150, -300], [150, -60], [520, -170], 18),
    ],
  },
  [String.fromCodePoint(0x2209)]: {
    w: 700,
    strokes: [
      quadratic([540, -430], [170, -540], [170, -300], 18),
      quadratic([170, -300], [170, -60], [540, -170], 18),
      line([[130, -500], [570, -90]]),
    ],
  },
  [String.fromCodePoint(0x2282)]: {
    w: 700,
    strokes: [
      quadratic([540, -460], [150, -540], [150, -300], 18),
      quadratic([150, -300], [150, -60], [540, -140], 18),
    ],
  },
  [String.fromCodePoint(0x2286)]: {
    w: 700,
    strokes: [
      quadratic([540, -460], [150, -540], [150, -300], 18),
      quadratic([150, -300], [150, -60], [540, -140], 18),
      line([[160, -70], [550, -70]]),
    ],
  },
  [String.fromCodePoint(0x222a)]: {
    w: 700,
    strokes: [
      line([[130, -470], [130, -260]]),
      quadratic([130, -260], [350, -30], [570, -260], 18),
      line([[570, -260], [570, -470]]),
    ],
  },
  [String.fromCodePoint(0x2229)]: {
    w: 700,
    strokes: [
      line([[130, -100], [130, -310]]),
      quadratic([130, -310], [350, -540], [570, -310], 18),
      line([[570, -310], [570, -100]]),
    ],
  },
  [String.fromCodePoint(0x2227)]: {
    w: 700,
    strokes: [line([[120, -100], [350, -490], [580, -100]])],
  },
  [String.fromCodePoint(0x2228)]: {
    w: 700,
    strokes: [line([[120, -490], [350, -100], [580, -490]])],
  },
};

export const customMathGlyphData = Object.fromEntries(
  Object.entries(glyphs).map(([character, path]) => [
    character,
    makeGlyph(path),
  ]),
);





