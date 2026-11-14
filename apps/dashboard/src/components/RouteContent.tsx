import { Component, Suspense, type ReactNode } from 'react';
import { useLocation } from 'react-router-dom';

class RouteErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  render() {
    if (this.state.failed) {
      return <div role="alert" className="space-y-3 p-6">
        <p>This page could not load. Check your connection to the local dashboard and try again.</p>
        <button type="button" className="rounded bg-cyan-700 px-4 py-2 text-white"
          onClick={() => window.location.reload()}>Reload page</button>
      </div>;
    }
    return this.props.children;
  }
}

// Keep navigation and runtime controls mounted while page chunks are loading.
export function RouteContent({ children }: { children: ReactNode }) {
  const { pathname } = useLocation();
  return <RouteErrorBoundary key={pathname}>
    <Suspense fallback={<p role="status" className="p-6">Loading page…</p>}>
      {children}
    </Suspense>
  </RouteErrorBoundary>;
}
