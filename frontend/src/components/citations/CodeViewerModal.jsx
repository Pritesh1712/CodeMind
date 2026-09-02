/**
 * components/citations/CodeViewerModal.jsx — Code Snippet Viewer
 * 
 * Modal that shows a citation's code with syntax highlighting.
 * Opens when the user clicks a citation badge.
 */

import { useEffect } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

export default function CodeViewerModal({ citation, onClose }) {
  const { file_path, start_line, end_line, code, language, symbol_name } = citation;

  // Close modal on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  return (
    <div className="modal-overlay" onClick={onClose}>
      {/* Stop propagation so clicking inside the modal doesn't close it */}
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        
        {/* Header */}
        <div className="modal-header">
          <div>
            <div className="modal-title">
              📄 {file_path}:{start_line}-{end_line}
            </div>
            {symbol_name && (
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
                Symbol: {symbol_name}
              </div>
            )}
          </div>
          <button className="modal-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        {/* Code */}
        <div className="modal-body">
          <SyntaxHighlighter
            language={language || 'text'}
            style={oneDark}
            showLineNumbers
            startingLineNumber={start_line}
            customStyle={{
              margin: 0,
              borderRadius: 0,
              fontSize: '13px',
              fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
              background: '#0d1117',
              minHeight: '100px',
            }}
          >
            {code || '// No code available'}
          </SyntaxHighlighter>
        </div>
      </div>
    </div>
  );
}
