/**
 * components/ui/MarkdownRenderer.jsx — Markdown with Syntax Highlighting
 * 
 * Renders markdown text with:
 *   - Clean, syntax-highlighted code blocks with Copy button
 *   - GitHub-Flavored Markdown (tables, lists, blockquotes)
 *   - Strips internal LLM brackets for pristine presentation
 */

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

// Custom dark theme that ensures no individual token background boxes
const codeStyle = {
  ...oneDark,
  'pre[class*="language-"]': {
    ...oneDark['pre[class*="language-"]'],
    background: '#0d1117',
    margin: 0,
    padding: '16px',
    fontSize: '13.5px',
    lineHeight: '1.6',
    fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
    border: 'none',
    boxShadow: 'none',
  },
  'code[class*="language-"]': {
    ...oneDark['code[class*="language-"]'],
    background: 'transparent',
    fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
    fontSize: '13.5px',
    lineHeight: '1.6',
    textShadow: 'none',
  },
};

function CodeBlock({ language, codeString, ...props }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(codeString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="code-block-wrapper">
      <div className="code-block-header">
        <span className="code-block-lang">{language || 'code'}</span>
        <button
          className="code-copy-btn"
          onClick={handleCopy}
          title="Copy code"
          type="button"
        >
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <SyntaxHighlighter
        style={codeStyle}
        language={language || 'text'}
        PreTag="div"
        customStyle={{
          background: '#0d1117',
          padding: '14px 16px',
          margin: 0,
          borderRadius: 0,
        }}
        codeTagProps={{
          style: {
            background: 'transparent',
            padding: 0,
            border: 'none',
          }
        }}
        {...props}
      >
        {codeString}
      </SyntaxHighlighter>
    </div>
  );
}

export default function MarkdownRenderer({ content }) {
  // Clean up any internal raw LLM citation markers (like 【1†L856-L870】 or 【2†source】)
  const cleanedContent = (content || '').replace(/【[^】]+】/g, '');

  return (
    <div className="markdown-content">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Code renderer (inline vs multi-line)
          code({ node, inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '');
            const language = match ? match[1] : '';
            const codeString = String(children).replace(/\n$/, '');

            if (!inline && (language || codeString.includes('\n'))) {
              return (
                <CodeBlock
                  language={language}
                  codeString={codeString}
                  {...props}
                />
              );
            }

            return (
              <code className="inline-code" {...props}>
                {children}
              </code>
            );
          },

          // Tables wrapper for responsive horizontal scrolling
          table({ children, ...props }) {
            return (
              <div className="table-responsive">
                <table {...props}>{children}</table>
              </div>
            );
          },

          // Open links in new tab safely
          a({ href, children }) {
            return (
              <a href={href} target="_blank" rel="noopener noreferrer">
                {children}
              </a>
            );
          },
        }}
      >
        {cleanedContent}
      </ReactMarkdown>
    </div>
  );
}
