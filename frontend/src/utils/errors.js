/**
 * Error Handling Utilities
 * 
 * Provides utilities for parsing and formatting API errors,
 * and managing error state in components.
 */

/**
 * Parse API error response into user-friendly message
 */
export function parseApiError(error) {
  // If error is already a structured object from our API
  if (error?.code && error?.detail) {
    return {
      code: error.code,
      message: error.detail,
      details: error,
    };
  }

  // If error has a message property
  if (error?.message) {
    return {
      code: 'UNKNOWN_ERROR',
      message: error.message,
      details: error,
    };
  }

  // If error is a string
  if (typeof error === 'string') {
    return {
      code: 'UNKNOWN_ERROR',
      message: error,
      details: {},
    };
  }

  // Default error
  return {
    code: 'UNKNOWN_ERROR',
    message: 'An unexpected error occurred',
    details: error || {},
  };
}

/**
 * Get user-friendly error message based on error code
 */
export function getErrorMessage(errorCode, defaultMessage) {
  const messages = {
    CONCEPT_NOT_FOUND: 'The requested concept could not be found. It may have been deleted.',
    EVALUATION_EXISTS: 'This concept has already been evaluated. Delete and recreate to re-evaluate.',
    EVALUATION_NOT_FOUND: 'No evaluation found for this concept. Please run evaluation first.',
    VALIDATION_ERROR: 'The data you provided is invalid. Please check your input.',
    VECTOR_STORE_ERROR: 'Vector database is temporarily unavailable. Please try again later.',
    LLM_SERVICE_ERROR: 'AI service is temporarily unavailable. Please try again later.',
    DATABASE_ERROR: 'Database error occurred. Please try again.',
    RATE_LIMIT_EXCEEDED: 'Too many requests. Please wait a moment and try again.',
    SERVICE_UNAVAILABLE: 'Service is temporarily unavailable. Please try again later.',
    INTERNAL_ERROR: 'An internal error occurred. Please try again or contact support.',
    NETWORK_ERROR: 'Network connection failed. Please check your internet connection.',
  };

  return messages[errorCode] || defaultMessage || 'An error occurred';
}

/**
 * Check if error is a network error
 */
export function isNetworkError(error) {
  return (
    error instanceof TypeError ||
    error?.message?.includes('fetch') ||
    error?.message?.includes('network') ||
    error?.code === 'NETWORK_ERROR'
  );
}

/**
 * Check if error is a client error (4xx)
 */
export function isClientError(status) {
  return status >= 400 && status < 500;
}

/**
 * Check if error is a server error (5xx)
 */
export function isServerError(status) {
  return status >= 500 && status < 600;
}

/**
 * Retry helper for failed requests
 */
export async function retryWithBackoff(fn, maxRetries = 3, initialDelay = 1000) {
  let lastError;
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      
      // Don't retry client errors (4xx)
      if (error?.status && isClientError(error.status)) {
        throw error;
      }
      
      // Wait with exponential backoff
      if (attempt < maxRetries - 1) {
        const delay = initialDelay * Math.pow(2, attempt);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  
  throw lastError;
}

/**
 * Format error for display
 */
export function formatErrorDisplay(error) {
  const parsed = parseApiError(error);
  const userMessage = getErrorMessage(parsed.code, parsed.message);
  
  return {
    title: getErrorTitle(parsed.code),
    message: userMessage,
    code: parsed.code,
    technicalDetails: parsed.details,
  };
}

/**
 * Get error title based on code
 */
function getErrorTitle(code) {
  const titles = {
    CONCEPT_NOT_FOUND: 'Concept Not Found',
    EVALUATION_EXISTS: 'Already Evaluated',
    EVALUATION_NOT_FOUND: 'Evaluation Not Found',
    VALIDATION_ERROR: 'Validation Error',
    VECTOR_STORE_ERROR: 'Database Unavailable',
    LLM_SERVICE_ERROR: 'AI Service Unavailable',
    DATABASE_ERROR: 'Database Error',
    RATE_LIMIT_EXCEEDED: 'Rate Limit Exceeded',
    SERVICE_UNAVAILABLE: 'Service Unavailable',
    INTERNAL_ERROR: 'Internal Error',
    NETWORK_ERROR: 'Network Error',
  };

  return titles[code] || 'Error';
}

/**
 * Create an API error from response
 */
export class ApiError extends Error {
  constructor(status, data, message) {
    super(message || data?.detail || 'API request failed');
    this.name = 'ApiError';
    this.status = status;
    this.code = data?.code || 'UNKNOWN_ERROR';
    this.details = data || {};
  }
}
