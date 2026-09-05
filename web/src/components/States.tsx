import type { ReactNode } from 'react'

export function Spinner({ className = 'h-4 w-4' }: { className?: string }) {
  return (
    <svg className={`animate-spin ${className}`} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2.5" opacity=".2" />
      <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  )
}

export function Skeleton({ className = '' }: { className?: string }) {
  return (
    <div className={`relative overflow-hidden rounded-lg bg-raise/60 ${className}`}>
      <div className="absolute inset-0 animate-sweep bg-gradient-to-r from-transparent via-white/[.05] to-transparent" />
    </div>
  )
}

export function Empty({ title, hint, icon }: { title: string; hint?: string; icon?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-line px-6 py-14 text-center">
      {icon ?? <div className="clapper mb-2 h-[6px] w-16 opacity-35" />}
      <p className="text-sm font-medium text-dim">{title}</p>
      {hint && <p className="max-w-sm text-xs leading-relaxed text-faint">{hint}</p>}
    </div>
  )
}

export function ErrorBox({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div
      role="alert"
      className="flex flex-wrap items-center gap-3 rounded-xl border border-ng/40 bg-ng/10 px-4 py-3 text-[13px] text-ng"
    >
      <svg viewBox="0 0 20 20" className="h-4 w-4 shrink-0" fill="currentColor" aria-hidden="true">
        <path d="M10 2 1 18h18L10 2Zm0 5.5a.9.9 0 0 1 .9.9v4a.9.9 0 1 1-1.8 0v-4a.9.9 0 0 1 .9-.9Zm0 8.4a1.05 1.05 0 1 1 0-2.1 1.05 1.05 0 0 1 0 2.1Z" />
      </svg>
      <span className="min-w-0 flex-1 break-words text-ink/90">{message}</span>
      {onRetry && (
        <button className="btn h-7 border-ng/40 px-2.5 py-0 text-[12px]" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  )
}
