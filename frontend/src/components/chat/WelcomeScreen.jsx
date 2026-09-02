/**
 * components/chat/WelcomeScreen.jsx — Empty State
 * 
 * Shown when there are no messages yet in the current chat.
 * Displays example questions to help users get started.
 */

const EXAMPLE_QUESTIONS = [
  {
    icon: '🏗️',
    text: 'How does the overall architecture work?',
  },
  {
    icon: '🔐',
    text: 'How is authentication implemented?',
  },
  {
    icon: '🗄️',
    text: 'Explain the database schema and models.',
  },
  {
    icon: '🔍',
    text: 'Where is the main entry point of this application?',
  },
  {
    icon: '⚡',
    text: 'How are API requests handled and routed?',
  },
  {
    icon: '🐛',
    text: 'How is error handling done throughout the codebase?',
  },
];

export default function WelcomeScreen({ repoName, onSelectQuestion }) {
  return (
    <div className="welcome-screen">
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🧠</div>
        <h1 className="welcome-title">
          Ask about {repoName || 'your repository'}
        </h1>
        <p className="welcome-subtitle">
          I've indexed the codebase and I'm ready to answer questions<br />
          using actual code evidence with exact file and line citations.
        </p>
      </div>

      <div className="example-questions">
        {EXAMPLE_QUESTIONS.map((q, index) => (
          <button
            key={index}
            className="example-question-card"
            onClick={() => onSelectQuestion(q.text)}
            id={`example-question-${index}`}
          >
            <div className="example-question-icon">{q.icon}</div>
            <div className="example-question-text">{q.text}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
