/**
 * components/citations/CitationBadge.jsx — Clickable Text-Only Citation Badge
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
        type="button"
      >
        <span className="citation-text">{label}</span>
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
