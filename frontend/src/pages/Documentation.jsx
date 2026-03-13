import { motion } from 'framer-motion';
import { ExternalLink, Code, BookOpen } from 'lucide-react';

export default function Documentation() {
  const endpoints = [
    {
      method: 'GET',
      path: '/api/v1/concepts',
      description: 'List all concepts (paginated)',
      params: 'page, page_size, status',
    },
    {
      method: 'POST',
      path: '/api/v1/concepts',
      description: 'Create a new concept',
      body: { title: 'string', description: 'string', author: 'string?', tags: 'array?' },
    },
    {
      method: 'GET',
      path: '/api/v1/concepts/{id}',
      description: 'Get a single concept by ID',
    },
    {
      method: 'PUT',
      path: '/api/v1/concepts/{id}',
      description: 'Update a concept',
    },
    {
      method: 'DELETE',
      path: '/api/v1/concepts/{id}',
      description: 'Delete a concept',
    },
    {
      method: 'POST',
      path: '/api/v1/concepts/{id}/evaluate',
      description: 'Trigger RAG evaluation',
      response: 'Returns evaluation with retrieved_context',
    },
    {
      method: 'GET',
      path: '/api/v1/concepts/{id}/evaluation',
      description: 'Get evaluation result',
    },
    {
      method: 'POST',
      path: '/api/v1/reports',
      description: 'Upload and create a report from PDF (indexes chunks in ChromaDB)',
    },
    {
      method: 'GET',
      path: '/api/v1/reports',
      description: 'List persisted reports (SQLite-backed)',
      params: 'page, page_size',
    },
    {
      method: 'GET',
      path: '/api/v1/reports/index',
      description: 'Read indexed reports directly from vector-store metadata/content',
      params: 'query, page, page_size',
    },
    {
      method: 'GET',
      path: '/api/v1/reports/{id}',
      description: 'Get a single report with extracted content',
    },
    {
      method: 'PUT',
      path: '/api/v1/reports/{id}',
      description: 'Update report metadata/content and re-index vectors when needed',
    },
    {
      method: 'DELETE',
      path: '/api/v1/reports/{id}',
      description: 'Delete report and remove vectors from ChromaDB',
    },
  ];

  const methodColors = {
    GET: 'text-cockpit-secondary',
    POST: 'text-cockpit-primary',
    PUT: 'text-cockpit-success',
    DELETE: 'text-cockpit-danger',
  };

  return (
    <div className="min-h-screen">
      <section className="border-b border-cockpit-border bg-cockpit-panel">
        <div className="container mx-auto px-8 py-12">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="flex items-center gap-3 mb-4">
              <BookOpen className="w-8 h-8 text-cockpit-primary" />
              <h1 className="text-4xl font-display font-bold text-cockpit-primary">
                DOCUMENTATION
              </h1>
            </div>
            <p className="text-lg text-cockpit-text-secondary">
              API reference and integration guides
            </p>
          </motion.div>
        </div>
      </section>

      <section className="container mx-auto px-8 py-12">
        <div className="max-w-5xl space-y-8">
          {/* Swagger Link */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="panel"
          >
            <div className="panel-header">
              <h2 className="font-display font-bold uppercase tracking-wide flex items-center gap-2">
                <Code className="w-5 h-5" />
                Interactive API Documentation
              </h2>
            </div>
            <div className="p-6">
              <p className="text-cockpit-text-secondary mb-4">
                Explore the full API specification with try-it-out functionality via Swagger UI.
              </p>
              <a
                href="http://127.0.0.1:8001/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="btn-primary inline-flex items-center gap-2"
              >
                <ExternalLink className="w-4 h-4" />
                Open Swagger UI
              </a>
            </div>
          </motion.div>

          {/* Endpoints List */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="panel"
          >
            <div className="panel-header">
              <h2 className="font-display font-bold uppercase tracking-wide">
                API Endpoints
              </h2>
            </div>
            <div className="divide-y divide-cockpit-border">
              {endpoints.map((endpoint, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 + index * 0.05 }}
                  className="p-6 hover:bg-cockpit-highlight/30 transition-colors"
                >
                  <div className="flex items-start gap-4">
                    <span className={`font-mono font-bold text-sm ${methodColors[endpoint.method]} min-w-[60px]`}>
                      {endpoint.method}
                    </span>
                    <div className="flex-1">
                      <code className="text-sm text-cockpit-text-primary font-mono bg-cockpit-bg px-2 py-1 rounded">
                        {endpoint.path}
                      </code>
                      <p className="text-sm text-cockpit-text-secondary mt-2">
                        {endpoint.description}
                      </p>
                      {endpoint.params && (
                        <div className="mt-2 text-xs text-cockpit-text-muted font-mono">
                          Params: {endpoint.params}
                        </div>
                      )}
                      {endpoint.body && (
                        <div className="mt-2">
                          <pre className="text-xs bg-cockpit-bg border border-cockpit-border rounded p-3 text-cockpit-secondary font-mono overflow-x-auto">
                            {JSON.stringify(endpoint.body, null, 2)}
                          </pre>
                        </div>
                      )}
                      {endpoint.response && (
                        <div className="mt-2 text-xs text-cockpit-success font-mono">
                          → {endpoint.response}
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Usage Example */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="panel"
          >
            <div className="panel-header">
              <h2 className="font-display font-bold uppercase tracking-wide">
                Example Usage
              </h2>
            </div>
            <div className="p-6">
              <pre className="text-sm bg-cockpit-bg border border-cockpit-border rounded p-4 text-cockpit-secondary font-mono overflow-x-auto">
{`# Create a concept
curl -X POST http://127.0.0.1:8001/api/v1/concepts \\
  -H "Content-Type: application/json" \\
  -d '{
    "title": "Active diffuser flow control",
    "description": "Ground effect diffuser using synthetic jets...",
    "author": "Engineer",
    "tags": ["ground-effect", "active-aero"]
  }'

# Evaluate concept (returns with citations)
curl -X POST http://127.0.0.1:8001/api/v1/concepts/1/evaluate

# Retrieve evaluation
curl http://127.0.0.1:8001/api/v1/concepts/1/evaluation`}
              </pre>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  );
}
