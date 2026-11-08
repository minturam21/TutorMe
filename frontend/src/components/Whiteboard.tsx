
import "./Whiteboard.css";

const subjects = [
  {
    name: "Physics",
    icon: "⚛️",
    description: "Forces, motion, energy and more",
  },
  {
    name: "Mathematics",
    icon: "📐",
    description: "Algebra, calculus and geometry",
  },
  {
    name: "Chemistry",
    icon: "🧪",
    description: "Reactions, atoms and molecules",
  },
  {
    name: "Biology",
    icon: "🧬",
    description: "Cells, anatomy and life sciences",
  },
  {
    name: "Programming",
    icon: "💻",
    description: "Code, logic and algorithms",
  },
];

const examples = [
  "How does gravity work?",
  "Visualize integration",
  "Explain chemical bonding",
  "How does a human heart work?",
];

interface WhiteboardProps {
  onSelectTopic: (topic: string) => void;
}

export default function Whiteboard({ onSelectTopic }: WhiteboardProps) {
  return (
    <div className="wb-welcome">
      <div className="wb-welcome-content">
        <div className="wb-welcome-icon">✦</div>

        <span className="wb-eyebrow">TUTORME VISUAL LEARNING</span>

        <h1>
          Learn by seeing.
          <br />
          Understand by exploring.
        </h1>

        <p className="wb-description">
          Turn difficult concepts into visual explanations, diagrams, equations
          and interactive lessons.
        </p>

        <h3>What would you like to explore?</h3>

        <div className="wb-subject-grid">
          {subjects.map((subject) => (
            <button
              className="wb-subject-card"
              key={subject.name}
              type="button"
              onClick={() =>
                onSelectTopic(
                  `Teach me ${subject.name} with visual explanations`
                )
              }
            >
              <span className="wb-subject-icon">{subject.icon}</span>
              <strong>{subject.name}</strong>
              <span>{subject.description}</span>
            </button>
          ))}
        </div>

        <div className="wb-examples">
          <span>TRY EXPLORING</span>

          <div>
            {examples.map((example) => (
              <button
                className="wb-example"
                key={example}
                type="button"
                onClick={() => onSelectTopic(example)}
              >
                {example}
              </button>
            ))}
          </div>
        </div>

        <div className="wb-bottom-hint">
          <span>✧</span>
          Enter your topic in the input box below to start learning.
        </div>
      </div>
    </div>
  );
}
