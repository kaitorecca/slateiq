import { Component, type ErrorInfo, type ReactNode } from 'react'

/**
 * A screen that throws must not take the whole product down with it. Without
 * this, one bad API shape blanks the page and the header, nav and health dots
 * go with it.
 */
export class ErrorBoundary extends Component<
  { children: ReactNode; label?: string },
  { error: Error | null }
> {
  state = { error: null as Error | null }

  static getDerivedStateFromError(error: Error) {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('SlateIQ screen crashed', error, info.componentStack)
  }

  componentDidUpdate(prev: { children: ReactNode; label?: string }) {
    if (prev.label !== this.props.label && this.state.error) this.setState({ error: null })
  }

  render() {
    if (!this.state.error) return this.props.children
    return (
      <div className="flex h-full items-center justify-center p-8">
        <div className="card max-w-md space-y-3 p-5 text-center">
          <div className="clapper mx-auto h-[7px] w-16 opacity-70" />
          <h2 className="text-[15px] font-semibold text-ink">This screen hit a snag</h2>
          <p className="text-[12.5px] leading-relaxed text-dim">
            {this.state.error.message || 'Unexpected error.'}
          </p>
          <button
            type="button"
            onClick={() => this.setState({ error: null })}
            className="rounded-lg border border-slate/50 bg-slate/10 px-3 py-1.5 text-[12px] text-slate transition hover:bg-slate/20"
          >
            Try again
          </button>
        </div>
      </div>
    )
  }
}
