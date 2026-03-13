import { FileText, Calendar, Hash, User } from 'lucide-react';

export default function ReportDetail({ report }) {
  if (!report) {
    return (
      <div className="panel">
        <div className="p-8 text-center text-cockpit-text-muted">
          Select a report to inspect extracted content and metadata.
        </div>
      </div>
    );
  }

  return (
    <div className="panel">
      <div className="panel-header flex items-center gap-2">
        <FileText className="w-5 h-5 text-cockpit-primary" />
        <h3 className="text-lg font-display font-bold text-cockpit-primary">Report Detail</h3>
      </div>

      <div className="p-6 space-y-5">
        <div>
          <h4 className="text-xl font-display font-semibold text-cockpit-text-primary">{report.title}</h4>
          <p className="text-xs text-cockpit-text-muted font-mono mt-1">{report.source_filename}</p>
        </div>

        <div className="grid md:grid-cols-3 gap-3 text-xs font-mono text-cockpit-text-muted">
          <div className="metric">
            <div className="metric-value text-lg">{report.chunk_count}</div>
            <div className="metric-label">Indexed Chunks</div>
          </div>
          <div className="metric">
            <div className="flex items-center justify-center gap-2">
              <Calendar className="w-4 h-4" />
              <span>{new Date(report.updated_at).toLocaleDateString()}</span>
            </div>
            <div className="metric-label">Last Updated</div>
          </div>
          <div className="metric">
            <div className="flex items-center justify-center gap-2">
              <Hash className="w-4 h-4" />
              <span>ID {report.id}</span>
            </div>
            <div className="metric-label">Report ID</div>
          </div>
        </div>

        {report.author && (
          <div className="flex items-center gap-2 text-sm text-cockpit-text-secondary">
            <User className="w-4 h-4 text-cockpit-secondary" />
            <span>{report.author}</span>
          </div>
        )}

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

        <div>
          <h5 className="label">Extracted Content</h5>
          <div className="bg-cockpit-bg border border-cockpit-border rounded p-4 max-h-[420px] overflow-y-auto">
            <pre className="text-xs text-cockpit-text-secondary whitespace-pre-wrap font-mono leading-relaxed">
              {report.content}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
