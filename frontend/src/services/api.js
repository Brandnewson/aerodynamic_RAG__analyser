/**
 * API Service Layer
 * 
 * This is the frontend's "infrastructure" layer - all HTTP communication
 * with the backend is centralized here. Components never call fetch directly.
 */

const API_BASE = '/api/v1';

/**
 * Generic fetch wrapper with error handling
 */
async function apiCall(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  
  const config = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: `HTTP ${response.status}: ${response.statusText}`,
      }));
      throw new Error(error.detail || 'Request failed');
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    throw error;
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
