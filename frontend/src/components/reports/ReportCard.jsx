import { motion } from 'framer-motion';
import { Calendar, Edit, Trash2, Eye, User, Hash } from 'lucide-react';

export default function ReportCard({ report, onSelect, onEdit, onDelete }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="panel"
    >
      <div className="panel-header flex items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-display font-semibold text-cockpit-text-primary">
            {report.title}
          </h3>
          <p className="text-xs text-cockpit-text-muted font-mono mt-1">
            {report.source_filename}
          </p>
        </div>
        <span className="badge badge-status-submitted">REPORT</span>
      </div>

      <div className="p-6 space-y-4">
        <div className="grid gap-2 text-xs text-cockpit-text-muted font-mono">
          {report.author && (
            <div className="flex items-center gap-2">
              <User className="w-3 h-3" />
              <span>{report.author}</span>
            </div>
          )}
          <div className="flex items-center gap-2">
            <Calendar className="w-3 h-3" />
            <span>{new Date(report.created_at).toLocaleString()}</span>
          </div>
          <div className="flex items-center gap-2">
            <Hash className="w-3 h-3" />
            <span>{report.chunk_count} chunks indexed</span>
          </div>
        </div>

        {report.tags?.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {report.tags.map((tag) => (
              <span
                key={tag}
                className="px-2 py-1 bg-cockpit-bg rounded text-xs text-cockpit-secondary border border-cockpit-secondary/30 font-mono"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        <div className="flex items-center gap-2 pt-3 border-t border-cockpit-border">
          <button onClick={() => onSelect(report)} className="btn-secondary flex items-center gap-2">
            <Eye className="w-4 h-4" />
            View
          </button>
          <button onClick={() => onEdit(report)} className="btn-outline flex items-center gap-2">
            <Edit className="w-4 h-4" />
            Edit
          </button>
          <button onClick={() => onDelete(report)} className="btn-danger flex items-center gap-2 ml-auto">
            <Trash2 className="w-4 h-4" />
            Delete
          </button>
        </div>
      </div>
    </motion.div>
  );
}
