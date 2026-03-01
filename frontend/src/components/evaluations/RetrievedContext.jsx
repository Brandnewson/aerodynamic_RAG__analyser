import { motion } from 'framer-motion';
import { Database } from 'lucide-react';
import CitationCard from './CitationCard';

export default function RetrievedContext({ retrievedContext }) {
  if (!retrievedContext || retrievedContext.length === 0) {
    return (
      <div className="panel">
        <div className="p-8 text-center text-cockpit-text-muted">
          <Database className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>No retrieved context available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <h3 className="text-lg font-display font-bold text-cockpit-text-primary uppercase tracking-wide">
          Retrieved Literature
        </h3>
        <span className="text-sm text-cockpit-text-muted font-mono">
          {retrievedContext.length} sources
        </span>
      </motion.div>

      <div className="grid gap-4">
        {retrievedContext.map((chunk, index) => (
          <CitationCard key={index} chunk={chunk} index={index} />
        ))}
      </div>
    </div>
  );
}
