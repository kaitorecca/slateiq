import { useCallback, useEffect, useRef, useState } from 'react'
import { formatSql, tokenizeSql } from '../lib/sql'

/**
 * Syntax-highlighted SQL with an always-visible copy button and an explicit
 * wrap toggle. Long statements are the norm in the trace panel, so when the
 * block scrolls horizontally we show a fading right edge as the affordance
 * (QC #1, P2: "it scrolls, but nothing says so").
 */
export function SqlBlock({ sql, dense = false }: { sql: string; dense?: boolean }) {
  const [copied, setCopied] = useState(false)
  const [wrap, setWrap] = useState(false)
  const [overflow, setOverflow] = useState(false)
  const preRef = useRef<HTMLPreElement | null>(null)
  const pretty = formatSql(sql)

  const measure = useCallback(() => {
    const el = preRef.current
    if (!el) return
    setOverflow(!wrap && el.scrollWidth - el.clientWidth > 4 && el.scrollLeft < el.scrollWidth - el.clientWidth - 4)
  }, [wrap])

  useEffect(() => {
    measure()
    window.addEventListener('resize', measure)
    return () => window.removeEventListener('resize', measure)
  }, [measure, pretty])

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(sql)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1400)
    } catch {
      setCopied(false)
    }
  }

  const btn =
    'rounded-md border border-line bg-panel/95 px-2 py-1 text-[10px] font-medium text-dim shadow-sm backdrop-blur transition hover:border-slate/50 hover:text-slate focus-visible:border-slate/50'

  return (
    <div className="relative overflow-hidden rounded-lg border border-line bg-cell">
      <div className="absolute right-1.5 top-1.5 z-10 flex items-center gap-1">
        <button type="button" onClick={() => setWrap((w) => !w)} aria-pressed={wrap} className={btn}>
          {wrap ? 'No wrap' : 'Wrap'}
        </button>
        <button type="button" onClick={copy} aria-label={copied ? 'Copied SQL' : 'Copy SQL'} className={btn}>
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      {overflow && (
        <div
          className="pointer-events-none absolute bottom-0 right-0 top-0 z-[5] w-10 bg-gradient-to-l from-cell to-transparent"
          aria-hidden="true"
        />
      )}
      <pre
        ref={preRef}
        onScroll={measure}
        className={`font-mono leading-[1.55] text-ink/90 ${
          wrap ? 'whitespace-pre-wrap break-words' : 'overflow-x-auto'
        } ${dense ? 'px-2.5 pb-5 pt-8 text-[11px]' : 'px-3 pb-6 pt-9 text-[12px]'}`}
      >
        <code>
          {tokenizeSql(pretty).map((tk, i) => (
            <span key={i} className={tk.cls}>
              {tk.text}
            </span>
          ))}
        </code>
      </pre>
      {overflow && (
        <span className="pointer-events-none absolute bottom-1 right-2 z-10 font-mono text-[9px] uppercase tracking-wide text-faint">
          scroll →
        </span>
      )}
    </div>
  )
}
