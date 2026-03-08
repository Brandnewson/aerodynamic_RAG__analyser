import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Activity, CheckCircle, XCircle, RefreshCw, Database, Zap, Brain } from 'lucide-react';
import { healthApi } from '../services/api';

export default function HealthCheck() {
  const [health, setHealth] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [lastCheck, setLastCheck] = useState(null);

  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    setIsLoading(true);
    try {
      const response = await healthApi.check();
      setHealth(response);
      setLastCheck(new Date());
    } catch (error) {
      setHealth({ status: 'error', message: error.message, components: {} });
      setLastCheck(new Date());
    } finally {
      setIsLoading(false);
    }
  };

  const isHealthy = health?.status === 'ok';
  const isDegraded = health?.status === 'degraded';

  const getComponentStatus = (key) => {
    if (!health?.components) return { status: 'unknown', icon: '?', color: 'text-cockpit-text-muted' };
    
    const value = health.components[key];
    if (!value) return { status: 'unknown', icon: '?', color: 'text-cockpit-text-muted' };
    
    if (value.startsWith('error:')) {
      return { status: value, icon: '✗', color: 'text-cockpit-danger' };
    }
    
    return { status: value, icon: '✓', color: 'text-cockpit-success' };
  };

  const dbStatus = getComponentStatus('database');
  const vectorStatus = getComponentStatus('vector_store');
  const llmStatus = getComponentStatus('llm');

  return (
    <div className="min-h-screen">
      <section className="border-b border-cockpit-border bg-cockpit-panel">
        <div className="container mx-auto px-8 py-12">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="flex items-center gap-3 mb-4">
              <Activity className="w-8 h-8 text-cockpit-primary" />
              <h1 className="text-4xl font-display font-bold text-cockpit-primary">
                SYSTEM STATUS
              </h1>
            </div>
            <p className="text-lg text-cockpit-text-secondary">
              Real-time health monitoring and diagnostics
            </p>
          </motion.div>
        </div>
      </section>

      <section className="container mx-auto px-8 py-12">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Status Card */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="panel"
          >
            <div className={`panel-header ${isHealthy ? 'bg-cockpit-success/10' : isDegraded ? 'bg-yellow-500/10' : 'bg-cockpit-danger/10'}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {isHealthy ? (
                    <CheckCircle className="w-6 h-6 text-cockpit-success" />
                  ) : isDegraded ? (
                    <Activity className="w-6 h-6 text-yellow-500" />
                  ) : (
                    <XCircle className="w-6 h-6 text-cockpit-danger" />
                  )}
                  <h2 className="text-2xl font-display font-bold uppercase tracking-wide">
                    {isLoading ? 'Checking...' : isHealthy ? 'System Operational' : isDegraded ? 'System Degraded' : 'System Error'}
                  </h2>
                </div>
                <button
                  onClick={checkHealth}
                  disabled={isLoading}
                  className="btn-secondary flex items-center gap-2"
                >
                  <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                  Refresh
                </button>
              </div>
            </div>

            <div className="p-6">
              {isLoading ? (
                <div className="text-center py-8">
                  <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-cockpit-primary border-t-transparent"></div>
                  <p className="text-cockpit-text-muted mt-4 font-mono">
                    Performing health check...
                  </p>
                </div>
              ) : health ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-cockpit-text-secondary">API Status</span>
                    <span className={`font-display font-bold uppercase ${
                      isHealthy ? 'text-cockpit-success' : 
                      isDegraded ? 'text-yellow-500' : 
                      'text-cockpit-danger'
                    }`}>
                      {health.status}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-cockpit-text-secondary">Version</span>
                    <span className="font-mono text-cockpit-text-primary">
                      {health.version || 'unknown'}
                    </span>
                  </div>

                  {health.message && (
                    <div className="bg-cockpit-bg border border-cockpit-border rounded p-4">
                      <p className="text-sm text-cockpit-text-secondary font-mono">
                        {health.message}
                      </p>
                    </div>
                  )}

                  {lastCheck && (
                    <div className="text-xs text-cockpit-text-muted font-mono pt-4 border-t border-cockpit-border">
                      Last checked: {lastCheck.toLocaleTimeString()}
                    </div>
                  )}
                </div>
              ) : null}
            </div>
          </motion.div>

          {/* Component Status */}
          <div className="grid grid-cols-3 gap-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="panel"
            >
              <div className="p-6 text-center">
                <Database className="w-8 h-8 text-cockpit-secondary mx-auto mb-3" />
                <div className={`text-2xl font-display font-bold mb-1 ${dbStatus.color}`}>
                  {dbStatus.icon}
                </div>
                <div className="text-sm text-cockpit-text-muted font-display uppercase tracking-wider mb-2">
                  Database
                </div>
                <div className="text-xs text-cockpit-text-muted font-mono">
                  {dbStatus.status}
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="panel"
            >
              <div className="p-6 text-center">
                <Zap className="w-8 h-8 text-cockpit-primary mx-auto mb-3" />
                <div className={`text-2xl font-display font-bold mb-1 ${vectorStatus.color}`}>
                  {vectorStatus.icon}
                </div>
                <div className="text-sm text-cockpit-text-muted font-display uppercase tracking-wider mb-2">
                  Vector Store
                </div>
                <div className="text-xs text-cockpit-text-muted font-mono">
                  {vectorStatus.status}
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="panel"
            >
              <div className="p-6 text-center">
                <Brain className="w-8 h-8 text-yellow-500 mx-auto mb-3" />
                <div className={`text-2xl font-display font-bold mb-1 ${llmStatus.color}`}>
                  {llmStatus.icon}
                </div>
                <div className="text-sm text-cockpit-text-muted font-display uppercase tracking-wider mb-2">
                  AI Model
                </div>
                <div className="text-xs text-cockpit-text-muted font-mono">
                  {llmStatus.status}
                </div>
              </div>
            </motion.div>
          </div>

          {/* Endpoint Tests */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="panel"
          >
            <div className="panel-header">
              <h3 className="font-display font-bold uppercase tracking-wide">
                Quick Diagnostics
              </h3>
            </div>
            <div className="p-6 space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-cockpit-text-secondary">Backend API</span>
                <span className="text-cockpit-success font-mono">http://127.0.0.1:8001</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-cockpit-text-secondary">Swagger Docs</span>
                <a 
                  href="http://127.0.0.1:8001/docs" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-cockpit-secondary hover:text-cockpit-secondary/80 font-mono"
                >
                  /docs →
                </a>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-cockpit-text-secondary">Health Endpoint</span>
                <a 
                  href="http://127.0.0.1:8001/api/v1/health" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-cockpit-secondary hover:text-cockpit-secondary/80 font-mono"
                >
                  /api/v1/health →
                </a>
              </div>
            </div>
          </motion.div>

          {/* System Info */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="panel"
          >
            <div className="panel-header">
              <h3 className="font-display font-bold uppercase tracking-wide">
                System Information
              </h3>
            </div>
            <div className="p-6 space-y-2 text-sm font-mono">
              <div className="flex justify-between">
                <span className="text-cockpit-text-muted">Version</span>
                <span className="text-cockpit-text-primary">{health?.version || 'v0.1.0'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-cockpit-text-muted">Environment</span>
                <span className="text-cockpit-text-primary">Development</span>
              </div>
              <div className="flex justify-between">
                <span className="text-cockpit-text-muted">Build</span>
                <span className="text-cockpit-text-primary">2026.02.28</span>
              </div>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  );
}
