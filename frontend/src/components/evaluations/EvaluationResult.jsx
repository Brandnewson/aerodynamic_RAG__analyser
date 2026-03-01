import { motion } from 'framer-motion';
import { Brain, TrendingUp, Target, AlertTriangle, Link2, Loader2, Zap } from 'lucide-react';
import RetrievedContext from './RetrievedContext';

export default function EvaluationResult({ evaluation, isLoading }) {
  if (isLoading) {
    return (
      <div className="panel">
        <div className="p-12 text-center">
          <Loader2 className="w-12 h-12 mx-auto mb-4 text-cockpit-primary animate-spin" />
          <p className="text-lg font-display text-cockpit-text-primary mb-2">
            Running RAG Evaluation
          </p>
          <p className="text-sm text-cockpit-text-muted font-mono">
            Querying literature and analyzing concept...
          </p>
        </div>
      </div>
    );
  }

  if (!evaluation) {
    return (
      <div className="panel">
        <div className="p-8 text-center text-cockpit-text-muted">
          <Brain className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>No evaluation available yet</p>
          <p className="text-sm mt-2">Click "Evaluate" on a concept to begin</p>
        </div>
      </div>
    );
  }

  const metricsData = [
    {
      label: 'Novelty Score',
      value: evaluation.novelty_score,
      icon: TrendingUp,
      iconColor: 'text-cockpit-primary',
      textColor: 'text-cockpit-primary',
      barColor: 'bg-cockpit-primary',
    },
    {
      label: 'Confidence',
      value: evaluation.confidence_score,
      icon: Target,
      iconColor: 'text-cockpit-secondary',
      textColor: 'text-cockpit-secondary',
      barColor: 'bg-cockpit-secondary',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-6">
        {metricsData.map((metric, index) => (
          <motion.div
            key={metric.label}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.1 }}
            className="metric hud-element"
          >
            <div className="flex items-center justify-center gap-2 mb-2">
              <metric.icon className={`w-5 h-5 ${metric.iconColor}`} />
              <div className="metric-label">{metric.label}</div>
            </div>
            <div className={`metric-value ${metric.textColor}`}>
              {(metric.value * 100).toFixed(0)}%
            </div>
            <div className="h-2 bg-cockpit-bg rounded-full overflow-hidden mt-3">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${metric.value * 100}%` }}
                transition={{ delay: index * 0.1 + 0.2, duration: 0.8, ease: 'easeOut' }}
                className={`h-full ${metric.barColor}`}
              />
            </div>
          </motion.div>
        ))}
      </div>

      {/* Mechanisms */}
      {evaluation.mechanisms && evaluation.mechanisms.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="panel"
        >
          <div className="panel-header flex items-center gap-2">
            <Brain className="w-5 h-5 text-cockpit-primary" />
            <h3 className="font-display font-bold uppercase tracking-wide">
              Identified Mechanisms
            </h3>
          </div>
          <div className="p-6">
            <ul className="space-y-2">
              {evaluation.mechanisms.map((mechanism, index) => (
                <motion.li
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.4 + index * 0.05 }}
                  className="flex items-start gap-3 text-sm text-cockpit-text-secondary"
                >
                  <span className="text-cockpit-primary font-mono text-xs mt-0.5">
                    [{index + 1}]
                  </span>
                  <span>{mechanism}</span>
                </motion.li>
              ))}
            </ul>
          </div>
        </motion.div>
      )}

      {/* Tradeoffs */}
      {evaluation.tradeoffs && Object.keys(evaluation.tradeoffs).length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="panel"
        >
          <div className="panel-header flex items-center gap-2">
            <Link2 className="w-5 h-5 text-cockpit-secondary" />
            <h3 className="font-display font-bold uppercase tracking-wide">
              Engineering Tradeoffs
            </h3>
          </div>
          <div className="p-6">
            <div className="grid gap-4">
              {Object.entries(evaluation.tradeoffs).map(([key, value], index) => (
                <motion.div
                  key={key}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.5 + index * 0.05 }}
                  className="bg-cockpit-bg border border-cockpit-border rounded p-4"
                >
                  <div className="text-xs text-cockpit-secondary font-display font-bold uppercase tracking-wider mb-1">
                    {key.replace(/_/g, ' ')}
                  </div>
                  <div className="text-sm text-cockpit-text-secondary">
                    {value}
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>
      )}

      {/* Regulatory Flags */}
      {evaluation.regulatory_flags && evaluation.regulatory_flags.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="panel border-cockpit-danger/30"
        >
          <div className="panel-header flex items-center gap-2 bg-cockpit-danger/10">
            <AlertTriangle className="w-5 h-5 text-cockpit-danger" />
            <h3 className="font-display font-bold uppercase tracking-wide text-cockpit-danger">
              Regulatory Considerations
            </h3>
          </div>
          <div className="p-6">
            <ul className="space-y-2">
              {evaluation.regulatory_flags.map((flag, index) => (
                <motion.li
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.6 + index * 0.05 }}
                  className="flex items-start gap-3 text-sm text-cockpit-danger"
                >
                  <span className="text-cockpit-danger font-mono text-xs mt-0.5">
                    ⚠
                  </span>
                  <span>{flag}</span>
                </motion.li>
              ))}
            </ul>
          </div>
        </motion.div>
      )}

      {/* Existing Implementations */}
      {evaluation.existing_implementations && evaluation.existing_implementations.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.55 }}
          className="panel border-cockpit-secondary/30"
        >
          <div className="panel-header flex items-center gap-2 bg-cockpit-secondary/10">
            <Zap className="w-5 h-5 text-cockpit-secondary" />
            <h3 className="font-display font-bold uppercase tracking-wide text-cockpit-secondary">
              Similar/Existing Implementations
            </h3>
          </div>
          <div className="p-6">
            <ul className="space-y-3">
              {evaluation.existing_implementations.map((implementation, index) => (
                <motion.li
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.56 + index * 0.05 }}
                  className="flex items-start gap-3 text-sm text-cockpit-text-secondary"
                >
                  <span className="text-cockpit-secondary font-mono text-xs mt-0.5 bg-cockpit-secondary/20 px-2 py-1 rounded">
                    →
                  </span>
                  <span>{implementation}</span>
                </motion.li>
              ))}
            </ul>
          </div>
        </motion.div>
      )}

      {/* Retrieved Context */}
      {evaluation.retrieved_context && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
        >
          <RetrievedContext retrievedContext={evaluation.retrieved_context} />
        </motion.div>
      )}
    </div>
  );
}
