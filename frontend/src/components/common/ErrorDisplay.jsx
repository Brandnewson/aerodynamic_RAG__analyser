import { AlertCircle, RefreshCw, Home } from 'lucide-react';
import { formatErrorDisplay } from '../../utils/errors';

/**
 * Error Display Component
 * Shows formatted error messages with appropriate styling and actions
 */
export default function ErrorDisplay({ error, onRetry, onDismiss, className = '' }) {
  const formattedError = formatErrorDisplay(error);

  return (
    <div className={`bg-red-900/10 border-2 border-red-500/30 rounded-lg p-6 ${className}`}>
      <div className="flex items-start gap-4">
        <AlertCircle className="w-6 h-6 text-red-400 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-cockpit-text-primary mb-2">
            {formattedError.title}
          </h3>
          <p className="text-cockpit-text-secondary mb-4">
            {formattedError.message}
          </p>
          
          {formattedError.code && (
            <p className="text-xs text-cockpit-text-muted font-mono mb-4">
              Error Code: {formattedError.code}
            </p>
          )}

          <div className="flex gap-3">
            {onRetry && (
              <button
                onClick={onRetry}
                className="flex items-center gap-2 px-4 py-2 bg-cockpit-primary hover:bg-cockpit-primary/90 transition-colors rounded font-semibold text-black text-sm"
              >
                <RefreshCw className="w-4 h-4" />
                Retry
              </button>
            )}
            {onDismiss && (
              <button
                onClick={onDismiss}
                className="px-4 py-2 border border-cockpit-border hover:border-cockpit-primary transition-colors rounded font-semibold text-cockpit-text-primary text-sm"
              >
                Dismiss
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Inline error message for form fields
 */
export function FieldError({ message, className = '' }) {
  if (!message) return null;

  return (
    <div className={`flex items-center gap-2 text-red-400 text-sm mt-1 ${className}`}>
      <AlertCircle className="w-4 h-4" />
      <span>{message}</span>
    </div>
  );
}

/**
 * Empty state with optional error message
 */
export function EmptyState({ 
  title, 
  message, 
  icon: Icon = Home,
  action,
  actionLabel,
  error 
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      {error ? (
        <AlertCircle className="w-16 h-16 text-red-400 mb-4" />
      ) : (
        <Icon className="w-16 h-16 text-cockpit-text-muted mb-4" />
      )}
      
      <h3 className="text-xl font-semibold text-cockpit-text-primary mb-2">
        {title}
      </h3>
      
      <p className="text-cockpit-text-secondary max-w-md mb-6">
        {message}
      </p>

      {action && actionLabel && (
        <button
          onClick={action}
          className="px-6 py-3 bg-cockpit-primary hover:bg-cockpit-primary/90 transition-colors rounded font-semibold text-black"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}

/**
 * Loading error with retry option
 */
export function LoadingError({ message, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <AlertCircle className="w-12 h-12 text-red-400 mb-4" />
      <p className="text-cockpit-text-primary mb-4">{message || 'Failed to load data'}</p>
      <button
        onClick={onRetry}
        className="flex items-center gap-2 px-4 py-2 bg-cockpit-primary hover:bg-cockpit-primary/90 transition-colors rounded font-semibold text-black"
      >
        <RefreshCw className="w-4 h-4" />
        Retry
      </button>
    </div>
  );
}
