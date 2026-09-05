export function SlateMark({ className = 'h-7 w-7' }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden="true">
      <rect x="1" y="1" width="30" height="30" rx="7" fill="#0E1013" stroke="#252A31" />
      <path d="M4.5 11.5h23v13a2 2 0 0 1-2 2h-19a2 2 0 0 1-2-2v-13z" fill="#1B1F25" />
      <path d="M4.2 5.9 26.6 3.2l.9 4.6L5.1 10.5z" fill="#E9E7E2" />
      <path
        d="M9 5.4 7.2 9.9M14 4.8 12.2 9.3M19 4.2 17.2 8.7M24 3.6 22.2 8.1"
        stroke="#0E1013"
        strokeWidth="1.8"
      />
      <rect x="8" y="15.5" width="15" height="1.8" rx=".9" fill="#F0B429" />
      <rect x="8" y="20" width="9" height="1.8" rx=".9" fill="#4A5058" />
    </svg>
  )
}

export function ClapperRule({ className = '' }: { className?: string }) {
  return <div aria-hidden="true" className={`clapper h-[3px] w-full opacity-70 ${className}`} />
}
