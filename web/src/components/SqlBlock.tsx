import { useState } from 'react'
import { formatSql, tokenizeSql } from '../lib/sql'

export function SqlBlock({ sql, dense = false }: { sql: string; dense?: boolean }) {
  const [copied, setCopied] = useState(false)
  const pretty = formatSql(sql)

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(sql)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1400)
    } catch {
      setCopied(false)
    }
  }

  return (
    <div className="group/sql relative overflow-hidden rounded-lg border border-line bg-cell">
      <button
        type="button"
        onClick={copy}
        aria-label="Copy SQL"
        className="absolute right-1.5 top-1.5 z-10 rounded-md border border-line bg-panel/90 px-2 py-1 text-[10px] font-medium text-dim opacity-0 transition focus-visible:opacity-100 group-hover/sql:opacity-100 hover:border-slate/50 hover:text-slate"
      >
        {copied ? 'Copied' : 'Copy'}
      </button>
      <pre
        className={`overflow-x-auto font-mono leading-[1.55] text-ink/90 ${
          dense ? 'p-2.5 text-[11px]' : 'p-3 text-[12px]'
        }`}
      >
        <code>
          {tokenizeSql(pretty).map((tk, i) => (
            <span key={i} className={tk.cls}>
              {tk.text}
            </span>
          ))}
        </code>
      </pre>
    </div>
  )
}
