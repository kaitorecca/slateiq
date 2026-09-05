import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export function Markdown({ children, className = '' }: { children: string; className?: string }) {
  return (
    <div className={`prose-slate-dark ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ node: _node, ...p }) => <a {...p} target="_blank" rel="noreferrer noopener" />,
          table: ({ node: _node, ...p }) => (
            <div className="-mx-1 overflow-x-auto">
              <table {...p} />
            </div>
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  )
}
