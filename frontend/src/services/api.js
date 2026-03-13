/**
 * API Service Layer
 * 
 * This is the frontend's "infrastructure" layer - all HTTP communication
 * with the backend is centralized here. Components never call fetch directly.
 */

import { ApiError, isNetworkError } from '../utils/errors';

const API_BASE = '/api/v1';

/**
 * Generic fetch wrapper with enhanced error handling
 */
async function apiCall(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const isFormData = options.body instanceof FormData;
  
  const config = {
    ...options,
    headers: {
      ...options.headers,
    },
  };

  if (!isFormData && !config.headers['Content-Type']) {
    config.headers['Content-Type'] = 'application/json';
  }

  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      // Parse error response
      let errorData;
      try {
        errorData = await response.json();
      } catch {
        errorData = {
          detail: `HTTP ${response.status}: ${response.statusText}`,
          code: 'HTTP_ERROR',
        };
      }
      
      // Throw structured ApiError
      throw new ApiError(
        response.status,
        errorData,
        errorData.detail || errorData.message
      );
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    
    // If it's already an ApiError, re-throw it
    if (error instanceof ApiError) {
      throw error;
    }
    
    // Handle network errors
    if (isNetworkError(error)) {
      throw new ApiError(0, {
        code: 'NETWORK_ERROR',
        detail: 'Network connection failed. Please check your internet connection.',
      });
    }
    
    // Handle other errors
    throw new ApiError(0, {
      code: 'UNKNOWN_ERROR',
      detail: error.message || 'An unexpected error occurred',
    });
  }
}

// ============================================================================
// Concepts API
// ============================================================================

export const conceptsApi = {
  /**
   * List all concepts with optional pagination and filtering
   */
  list: async ({ page = 1, pageSize = 50, status = null } = {}) => {
    const params = new URLSearchParams({ page, page_size: pageSize });
    if (status) params.append('status', status);
    
    return apiCall(`/concepts?${params}`);
  },

  /**
   * Get a single concept by ID
   */
  get: async (id) => {
    return apiCall(`/concepts/${id}`);
  },

  /**
   * Create a new concept
   */
  create: async (data) => {
    return apiCall('/concepts', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Update an existing concept
   */
  update: async (id, data) => {
    return apiCall(`/concepts/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete a concept
   */
  delete: async (id) => {
    return apiCall(`/concepts/${id}`, {
      method: 'DELETE',
    });
  },
};

// ============================================================================
// Evaluations API
// ============================================================================

export const evaluationsApi = {
  /**
   * Trigger RAG evaluation for a concept
   */
  evaluate: async (conceptId) => {
    return apiCall(`/concepts/${conceptId}/evaluate`, {
      method: 'POST',
    });
  },

  /**
   * Get the evaluation result for a concept
   */
  get: async (conceptId) => {
    return apiCall(`/concepts/${conceptId}/evaluation`);
  },
};

// ============================================================================
// Reports API
// ============================================================================

export const reportsApi = {
  /**
   * List all reports with optional pagination
   */
  list: async ({ page = 1, pageSize = 50 } = {}) => {
    const params = new URLSearchParams({ page, page_size: pageSize });
    return apiCall(`/reports?${params}`);
  },

  /**
   * Get a single report by ID
   */
  get: async (id) => {
    return apiCall(`/reports/${id}`);
  },

  /**
   * Upload and create a report using multipart form data
   */
  create: async (formData) => {
    return apiCall('/reports', {
      method: 'POST',
      body: formData,
    });
  },

  /**
   * Update report metadata/content
   */
  update: async (id, data) => {
    return apiCall(`/reports/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete a report
   */
  delete: async (id) => {
    return apiCall(`/reports/${id}`, {
      method: 'DELETE',
    });
  },
};

// ============================================================================
// Health API
// ============================================================================

export const healthApi = {
  /**
   * Check API health
   */
  check: async () => {
    return apiCall('/health');
  },
};
