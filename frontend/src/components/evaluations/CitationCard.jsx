import { motion } from 'framer-motion';
import { ExternalLink, BookOpen, FileText } from 'lucide-react';

export default function CitationCard({ chunk, index }) {
  const { citation, text, similarity_score, chunk_index } = chunk;

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1 }}
      className="panel hover:border-cockpit-secondary/50 transition-all duration-300"
    >
      <div className="p-5">
        {/* Header with similarity */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-cockpit-secondary" />
            <span className="text-xs font-mono text-cockpit-text-muted">
              REF {index + 1}
            </span>
          </div>
          <div className="text-right">
            <div className="text-lg font-bold text-cockpit-secondary font-mono">
              {(similarity_score * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-cockpit-text-muted uppercase tracking-wider">
              Similarity
            </div>
          </div>
        </div>

        {/* Title */}
        <h4 className="font-display font-semibold text-cockpit-text-primary mb-2 leading-tight">
          {citation.title}
        </h4>

        {/* Authors */}
        <p className="text-sm text-cockpit-text-secondary mb-3">
          {citation.authors}
        </p>

        {/* Metadata row */}
        <div className="flex items-center gap-4 text-xs font-mono text-cockpit-text-muted mb-3 pb-3 border-b border-cockpit-border">
          {citation.arxiv_id && (
            <span className="flex items-center gap-1">
              <FileText className="w-3 h-3" />
              {citation.arxiv_id}
            </span>
          )}
          {citation.published && (
            <span>
              {new Date(citation.published).getFullYear()}
            </span>
          )}
          <span className="ml-auto">
            Chunk {chunk_index}
          </span>
        </div>

        {/* Excerpt */}
        <div className="bg-cockpit-bg/50 border border-cockpit-border rounded p-3 mb-3">
          <p className="text-sm text-cockpit-text-secondary leading-relaxed font-mono">
            {text.length > 250 ? `${text.substring(0, 250)}...` : text}
          </p>
        </div>

        {/* Link */}
        {citation.url && (
          <a
            href={citation.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-sm text-cockpit-secondary hover:text-cockpit-secondary/80 transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
            View on arXiv
          </a>
        )}
      </div>
    </motion.div>
  );
}
