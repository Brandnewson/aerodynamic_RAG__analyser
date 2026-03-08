import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

/**
 * Error Boundary Component
 * Catches JavaScript errors anywhere in the child component tree
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error Boundary caught an error:', error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-cockpit-bg flex items-center justify-center p-8">
          <div className="max-w-2xl w-full bg-cockpit-panel border-2 border-red-500/30 rounded-lg p-8">
            <div className="flex items-center gap-4 mb-6">
              <AlertTriangle className="w-12 h-12 text-red-400" />
              <div>
                <h1 className="text-2xl font-display font-bold text-cockpit-text mb-2">
                  Something Went Wrong
                </h1>
                <p className="text-cockpit-text-secondary">
                  The application encountered an unexpected error.
                </p>
              </div>
            </div>

            {this.state.error && (
              <div className="bg-black/30 rounded p-4 mb-6 border border-cockpit-border">
                <p className="text-red-400 font-mono text-sm mb-2">
                  {this.state.error.toString()}
                </p>
                {this.state.errorInfo && (
                  <details className="text-cockpit-text-secondary text-xs font-mono">
                    <summary className="cursor-pointer hover:text-cockpit-text">
                      Stack Trace
                    </summary>
                    <pre className="mt-2 overflow-auto max-h-64 whitespace-pre-wrap">
                      {this.state.errorInfo.componentStack}
                    </pre>
                  </details>
                )}
              </div>
            )}

            <div className="flex gap-4">
              <button
                onClick={this.handleReset}
                className="flex items-center gap-2 px-6 py-3 bg-cockpit-primary hover:bg-cockpit-primary-dark transition-colors rounded font-semibold text-black"
              >
                <RefreshCw className="w-4 h-4" />
                Try Again
              </button>
              <button
                onClick={() => window.location.href = '/'}
                className="px-6 py-3 border-2 border-cockpit-border hover:border-cockpit-primary transition-colors rounded font-semibold text-cockpit-text"
              >
                Go to Dashboard
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
