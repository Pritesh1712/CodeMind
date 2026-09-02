/**
 * components/citations/CitationBadge.jsx — Clickable Citation Badge
 * 
 * Displays a citation like:  📄 src/auth.py:42-67
 * Clicking it opens the CodeViewerModal showing that code.
 */

import { useState } from 'react';
import CodeViewerModal from './CodeViewerModal';

export default function CitationBadge({ citation }) {
  const [isOpen, setIsOpen] = useState(false);

  const label = `${citation.file_path}:${citation.start_line}-${citation.end_line}`;

  return (
    <>
      <button
        className="citation-badge"
        onClick={() => setIsOpen(true)}
        title="Click to view source code"
        id={`citation-${citation.file_path}-${citation.start_line}`}
      >
        📄 {label}
      </button>

      {isOpen && (
        <CodeViewerModal
          citation={citation}
          onClose={() => setIsOpen(false)}
        />
      )}
    </>
  );
}
