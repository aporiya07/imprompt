import { Component, type ErrorInfo, type ReactNode } from "react";
import { CircleAlert, RefreshCw } from "lucide-react";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

/** Last-resort boundary: a render crash shows a calm recovery state, never a blank screen. */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("ImPrompt render error", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <main className="setup">
          <div className="brand crash-brand">ImPrompt</div>
          <div className="card error-banner crash-card" role="alert">
            <span className="error-icon">
              <CircleAlert size={16} />
            </span>
            <div className="error-body">
              <div className="error-label">Something went wrong</div>
              <span className="error-msg">
                The workspace failed to render. Your saved history is unaffected; try again.
              </span>
              <details className="error-details">
                <summary>Technical details</summary>
                <pre>{this.state.error.message}</pre>
              </details>
            </div>
            <button
              className="btn small banner-action"
              onClick={() => {
                this.setState({ error: null });
                window.location.reload();
              }}
            >
              <RefreshCw className="btn-icon" />
              Try again
            </button>
          </div>
        </main>
      );
    }
    return this.props.children;
  }
}
