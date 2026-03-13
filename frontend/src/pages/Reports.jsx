import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Plus, RefreshCw, FolderOpen } from 'lucide-react';

import { reportsApi } from '../services/api';
import ReportCard from '../components/reports/ReportCard';
import ReportForm from '../components/reports/ReportForm';
import ReportDetail from '../components/reports/ReportDetail';

export default function Reports() {
  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [editingReport, setEditingReport] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const loadReports = async () => {
    setIsLoading(true);
    try {
      const response = await reportsApi.list({ pageSize: 100 });
      setReports(response.items || []);
    } catch (error) {
      console.error('Failed to load reports:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadReportDetail = async (reportId) => {
    try {
      const report = await reportsApi.get(reportId);
      setSelectedReport(report);
      document.getElementById('report-detail-section')?.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
      alert(`Failed to load report detail: ${error.message}`);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  const handleCreate = () => {
    setEditingReport(null);
    setShowForm(true);
  };

  const handleEdit = async (reportSummary) => {
    try {
      const full = await reportsApi.get(reportSummary.id);
      setEditingReport(full);
      setShowForm(true);
    } catch (error) {
      alert(`Failed to load report for edit: ${error.message}`);
    }
  };

  const handleSave = async (payload) => {
    try {
      if (editingReport) {
        const updated = await reportsApi.update(editingReport.id, payload);
        setSelectedReport(updated);
      } else {
        const created = await reportsApi.create(payload);
        setSelectedReport(created);
      }
      setShowForm(false);
      setEditingReport(null);
      await loadReports();
    } catch (error) {
      throw new Error(error.message || 'Failed to save report.');
    }
  };

  const handleDelete = async (report) => {
    if (!window.confirm(`Delete report "${report.title}"?`)) return;
    try {
      await reportsApi.delete(report.id);
      if (selectedReport?.id === report.id) {
        setSelectedReport(null);
      }
      await loadReports();
    } catch (error) {
      alert(`Failed to delete report: ${error.message}`);
    }
  };

  return (
    <div className="min-h-screen">
      <section className="border-b border-cockpit-border bg-gradient-to-b from-cockpit-panel to-cockpit-bg">
        <div className="container mx-auto px-8 py-12">
          <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="max-w-4xl">
            <div className="flex items-center gap-3 mb-4">
              <FolderOpen className="w-8 h-8 text-cockpit-primary" />
              <h1 className="text-4xl font-display font-bold text-cockpit-primary text-glow">REPORT VECTOR STORE</h1>
            </div>
            <p className="text-lg text-cockpit-text-secondary leading-relaxed">
              Upload PDF reports, maintain report metadata, and keep indexed chunks in sync with the vector database.
            </p>
          </motion.div>
        </div>
      </section>

      <section className="border-b border-cockpit-border">
        <div className="container mx-auto px-8 py-12">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl font-display font-bold text-cockpit-text-primary uppercase tracking-wide mb-2">
                Reports
              </h2>
              <p className="text-sm text-cockpit-text-muted font-mono">{reports.length} reports indexed</p>
            </div>

            <div className="flex items-center gap-3">
              <button onClick={loadReports} className="btn-outline flex items-center gap-2" disabled={isLoading}>
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
              <button onClick={handleCreate} className="btn-primary flex items-center gap-2">
                <Plus className="w-4 h-4" />
                Upload Report
              </button>
            </div>
          </div>

          {isLoading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-cockpit-primary border-t-transparent" />
            </div>
          ) : reports.length === 0 ? (
            <div className="panel">
              <div className="p-12 text-center text-cockpit-text-muted">
                No reports uploaded yet. Use "Upload Report" to index your first PDF.
              </div>
            </div>
          ) : (
            <div className="grid gap-6">
              {reports.map((report) => (
                <ReportCard
                  key={report.id}
                  report={report}
                  onSelect={(item) => loadReportDetail(item.id)}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                />
              ))}
            </div>
          )}
        </div>
      </section>

      <section id="report-detail-section" className="bg-cockpit-bg">
        <div className="container mx-auto px-8 py-12">
          <ReportDetail report={selectedReport} />
        </div>
      </section>

      {showForm && (
        <ReportForm
          report={editingReport}
          onSave={handleSave}
          onCancel={() => {
            setShowForm(false);
            setEditingReport(null);
          }}
        />
      )}
    </div>
  );
}
