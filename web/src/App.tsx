import { Suspense, lazy, useEffect } from 'react'
import { getHealth } from './lib/api'
import { usePoll, useHashRoute } from './lib/hooks'
import { NAV, Rail } from './components/Rail'
import { HealthDots } from './components/HealthDots'
import { SlateMark } from './components/Brand'
import { Ask } from './screens/Ask'
import { Spinner } from './components/States'

const Takes = lazy(() => import('./screens/Takes').then((m) => ({ default: m.Takes })))
const Health = lazy(() => import('./screens/Health').then((m) => ({ default: m.Health })))
const About = lazy(() => import('./screens/About').then((m) => ({ default: m.About })))

function ScreenFallback() {
  return (
    <div className="flex h-full items-center justify-center text-faint">
      <Spinner className="h-5 w-5" />
    </div>
  )
}

export default function App() {
  const [route, nav] = useHashRoute('ask')
  const { data: health, error: healthError } = usePoll(getHealth, 20000)
  const current = NAV.find((n) => n.id === route) ?? NAV[0]

  useEffect(() => {
    document.title = `SlateIQ — ${current.label}`
  }, [current.label])

  return (
    <div className="flex h-full flex-col overflow-hidden md:flex-row">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-3 focus:top-3 focus:z-[100] focus:rounded-lg focus:border focus:border-slate/60 focus:bg-panel focus:px-3 focus:py-2 focus:text-[13px]"
      >
        Skip to content
      </a>

      <Rail route={current.id} onNav={nav} />

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex shrink-0 items-center gap-3 border-b border-line bg-cell/70 px-4 py-2.5 backdrop-blur sm:px-8">
          <div className="flex items-center gap-2 md:hidden">
            <SlateMark className="h-6 w-6" />
            <span className="text-[14px] font-semibold text-ink">SlateIQ</span>
          </div>
          <div className="hidden min-w-0 md:block">
            <div className="truncate text-[13px] font-medium text-ink">{current.label}</div>
            <div className="truncate text-[11px] text-faint">{current.hint}</div>
          </div>
          <div className="ml-auto flex items-center gap-3">
            <HealthDots health={health} error={healthError} />
          </div>
        </header>

        <main id="main" className="min-h-0 flex-1">
          <Suspense fallback={<ScreenFallback />}>
            {current.id === 'ask' && <Ask />}
            {current.id === 'takes' && <Takes />}
            {current.id === 'health' && <Health />}
            {current.id === 'about' && <About />}
          </Suspense>
        </main>
      </div>
    </div>
  )
}
