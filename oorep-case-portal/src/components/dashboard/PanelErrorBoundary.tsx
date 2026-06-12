"use client";

/**
 * PanelErrorBoundary.tsx
 * Error boundary for dashboard panel resilience
 */

import React, { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  panelName?: string;
  onRetry?: () => void;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
}

export default class PanelErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error(`PanelErrorBoundary caught error in ${this.props.panelName}:`, error, errorInfo);
    this.setState({ error, errorInfo });
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
    this.props.onRetry?.();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="bg-white rounded-lg border border-red-200 shadow-sm p-6">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center shrink-0">
              <svg className="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900">
                {this.props.panelName || 'Panel'} failed to load
              </h3>
              <p className="text-sm text-gray-500 mt-1">
                Something went wrong while rendering this panel. You can try refreshing it.
              </p>
              
              {this.state.error && (
                <div className="mt-3 p-3 bg-gray-50 rounded text-xs text-gray-600 font-mono overflow-x-auto">
                  {this.state.error.message}
                </div>
              )}
              
              <div className="flex gap-2 mt-4">
                <button
                  onClick={this.handleRetry}
                  className="px-3 py-1.5 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 transition"
                >
                  Retry
                </button>
                
                <button
                  onClick={() => window.location.reload()}
                  className="px-3 py-1.5 text-gray-600 text-sm hover:text-gray-900 transition"
                >
                  Reload Page
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * ErrorBoundaryWrapper - HOC for wrapping panels with error boundary
 */
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  panelName?: string
) {
  return function WrappedComponent(props: P) {
    return (
      <PanelErrorBoundary panelName={panelName}>
        <Component {...props} />
      </PanelErrorBoundary>
    );
  };
}
