/**
 * components/chat/WelcomeScreen.jsx — Text-Only Empty State
 * 
 * Displays categorized sample technical questions without icons.
 */

const EXAMPLE_QUESTIONS = [
  {
    category: 'ARCHITECTURE',
    text: 'How does the overall architecture work?',
  },
  {
    category: 'SECURITY',
    text: 'How is authentication implemented?',
  },
  {
    category: 'DATABASE',
    text: 'Explain the database schema and models.',
  },
  {
    category: 'ENTRY POINT',
    text: 'Where is the main entry point of this application?',
  },
  {
    category: 'API ROUTING',
    text: 'How are API requests handled and routed?',
  },
  {
    category: 'ERROR HANDLING',
    text: 'How is error handling done throughout the codebase?',
  },
];

export default function WelcomeScreen({ repoName, onSelectQuestion }) {
  return (
    <div className="welcome-screen">
      <div style={{ textAlign: 'center' }}>
        <div className="welcome-tag">READY TO EXPLORE</div>
        <h1 className="welcome-title">
          Ask about {repoName || 'your repository'}
        </h1>
        <p className="welcome-subtitle">
          CodeMind is ready to answer questions using exact code citations and file line ranges.
        </p>
      </div>

      <div className="example-questions">
        {EXAMPLE_QUESTIONS.map((q, index) => (
          <button
            key={index}
            className="example-question-card"
            onClick={() => onSelectQuestion(q.text)}
            id={`example-question-${index}`}
            type="button"
          >
            <div className="example-question-category">{q.category}</div>
            <div className="example-question-text">{q.text}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
