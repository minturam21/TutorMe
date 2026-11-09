import "./LessonLoading.css";

const paths = [
  "M 24 174 C 78 116, 105 222, 158 160 S 246 92, 302 145 S 390 218, 452 150",
  "M 96 84 C 142 112, 130 188, 190 196 S 265 166, 300 92",
  "M 284 190 C 330 142, 354 88, 414 104 S 485 170, 548 126",
  "M 442 52 C 470 92, 458 142, 520 180 S 610 196, 650 128",
  "M 590 82 C 630 46, 672 78, 690 118 S 734 166, 770 132",
  "M 170 160 C 206 126, 242 126, 276 150 S 336 214, 374 182",
];

const nodes = [
  [24, 174], [96, 84], [158, 160], [190, 196], [246, 92], [300, 145],
  [302, 92], [390, 218], [414, 104], [452, 150], [520, 180], [548, 126],
  [590, 82], [650, 128], [690, 118], [770, 132], [130, 188], [354, 88],
  [485, 170], [672, 78], [734, 166], [276, 150], [374, 182], [610, 196],
];

const links = [
  [24, 174, 96, 84], [96, 84, 158, 160], [158, 160, 246, 92],
  [158, 160, 190, 196], [190, 196, 276, 150], [246, 92, 302, 92],
  [246, 92, 300, 145], [300, 145, 354, 88], [300, 145, 390, 218],
  [354, 88, 414, 104], [390, 218, 452, 150], [414, 104, 452, 150],
  [452, 150, 520, 180], [452, 150, 548, 126], [520, 180, 610, 196],
  [548, 126, 590, 82], [548, 126, 650, 128], [590, 82, 672, 78],
  [650, 128, 690, 118], [690, 118, 770, 132], [650, 128, 734, 166],
  [130, 188, 190, 196], [276, 150, 354, 88], [374, 182, 452, 150],
];

export default function LessonLoading() {
  return (
    <section className="lesson-loading living-network" aria-live="polite" aria-busy="true">
      <div className="living-network__canvas" aria-hidden="true">
        <svg className="living-network__svg" viewBox="0 0 800 260" role="presentation">
          <defs>
            <linearGradient id="network-ink" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#7894E8" />
              <stop offset="52%" stopColor="#8A72D8" />
              <stop offset="100%" stopColor="#C28BD6" />
            </linearGradient>
            <radialGradient id="network-halo">
              <stop offset="0%" stopColor="#8D79E8" stopOpacity=".18" />
              <stop offset="100%" stopColor="#8D79E8" stopOpacity="0" />
            </radialGradient>
          </defs>
          <circle cx="400" cy="130" r="116" fill="url(#network-halo)" />
          <g className="living-network__links">
            {links.map(([x1, y1, x2, y2], index) => (
              <line key={index} x1={x1} y1={y1} x2={x2} y2={y2} />
            ))}
          </g>
          <g className="living-network__strokes">
            {paths.map((path, index) => (
              <path key={index} d={path} style={{ animationDelay: `${index * 420}ms` }} />
            ))}
          </g>
          <g className="living-network__nodes">
            {nodes.map(([cx, cy], index) => (
              <circle
                key={index}
                cx={cx}
                cy={cy}
                r={index % 5 === 0 ? 4.2 : index % 3 === 0 ? 2.8 : 2}
                style={{ animationDelay: `${index * 115}ms` }}
              />
            ))}
          </g>
        </svg>
      </div>
      <div className="living-network__copy">
        <span className="living-network__eyebrow">TUTOR ME · LIVE ACTIVITY</span>
        <h2>Your lesson is taking shape</h2>
        <div className="lesson-activity" role="list" aria-label="Lesson preparation activity">
          <div className="lesson-activity__item is-complete" role="listitem">
            <span className="lesson-activity__indicator" aria-hidden="true">✓</span>
            <span>Question received</span>
            <span className="lesson-activity__meta">DONE</span>
          </div>
          <div className="lesson-activity__item is-active" role="listitem">
            <span className="lesson-activity__indicator" aria-hidden="true"><span /></span>
            <span>Generating your lesson</span>
            <span className="lesson-activity__meta">IN PROGRESS</span>
          </div>
          <div className="lesson-activity__item is-pending" role="listitem">
            <span className="lesson-activity__indicator" aria-hidden="true">3</span>
            <span>Preparing the whiteboard</span>
            <span className="lesson-activity__meta">NEXT</span>
          </div>
        </div>
      </div>
    </section>
  );
}
