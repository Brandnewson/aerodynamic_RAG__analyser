import { motion } from 'framer-motion';
import { Calendar, User, Tag, Trash2, Edit, Play, Eye } from 'lucide-react';

export default function ConceptCard({ concept, onEdit, onDelete, onEvaluate, onViewEvaluation }) {
  const statusBadgeClass = {
    SUBMITTED: 'badge-status-submitted',
    ANALYSED: 'badge-status-analysed',
  }[concept.status] || 'badge-status-submitted';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="panel group hover:shadow-xl transition-shadow duration-300"
    >
      {/* Header */}
      <div className="panel-header flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-lg font-display font-semibold text-cockpit-text-primary">
              {concept.title}
            </h3>
            <span className={`badge ${statusBadgeClass}`}>
              {concept.status}
            </span>
          </div>
          
          {/* Metadata */}
          <div className="flex items-center gap-4 text-xs text-cockpit-text-muted font-mono">
            {concept.author && (
              <span className="flex items-center gap-1">
                <User className="w-3 h-3" />
                {concept.author}
              </span>
            )}
            <span className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {new Date(concept.created_at).toLocaleDateString()}
            </span>
            <span className="text-cockpit-text-muted/50">
              ID: {concept.id}
            </span>
          </div>
        </div>
      </div>

      {/* Description */}
      <div className="p-6">
        <p className="text-sm text-cockpit-text-secondary leading-relaxed mb-4">
          {concept.description}
        </p>

        {/* Tags */}
        {concept.tags && concept.tags.length > 0 && (
          <div className="flex items-center gap-2 flex-wrap mb-4">
            <Tag className="w-4 h-4 text-cockpit-text-muted" />
            {concept.tags.map(tag => (
              <span 
                key={tag}
                className="px-2 py-1 bg-cockpit-bg rounded text-xs text-cockpit-secondary border border-cockpit-secondary/30 font-mono"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2 pt-4 border-t border-cockpit-border">
          {concept.status === 'SUBMITTED' && (
            <button
              onClick={() => onEvaluate(concept)}
              className="btn-primary flex items-center gap-2"
            >
              <Play className="w-4 h-4" />
              Evaluate
            </button>
          )}
          
          {concept.status === 'ANALYSED' && (
            <button
              onClick={() => onViewEvaluation(concept)}
              className="btn-secondary flex items-center gap-2"
            >
              <Eye className="w-4 h-4" />
              View Results
            </button>
          )}
          
          <button
            onClick={() => onEdit(concept)}
            className="btn-outline flex items-center gap-2"
          >
            <Edit className="w-4 h-4" />
            Edit
          </button>
          
          <button
            onClick={() => onDelete(concept)}
            className="btn-danger flex items-center gap-2 ml-auto"
          >
            <Trash2 className="w-4 h-4" />
            Delete
          </button>
        </div>
      </div>
    </motion.div>
  );
}
