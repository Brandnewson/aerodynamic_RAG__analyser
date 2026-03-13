import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Upload, Save } from 'lucide-react';

export default function ReportForm({ report, onSave, onCancel }) {
  const [formData, setFormData] = useState({
    title: '',
    author: '',
    tags: '',
    content: '',
  });
  const [file, setFile] = useState(null);
  const [errors, setErrors] = useState({});
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (report) {
      setFormData({
        title: report.title || '',
        author: report.author || '',
        tags: report.tags ? report.tags.join(', ') : '',
        content: report.content || '',
      });
    }
  }, [report]);

  const validate = () => {
    const nextErrors = {};

    if (!formData.title || formData.title.trim().length < 3) {
      nextErrors.title = 'Title must be at least 3 characters.';
    }

    if (!report && !file) {
      nextErrors.file = 'Please upload a PDF file.';
    }

    if (!report && file && !file.name.toLowerCase().endsWith('.pdf')) {
      nextErrors.file = 'Only PDF files are supported.';
    }

    if (report && formData.content && formData.content.trim().length < 20) {
      nextErrors.content = 'Updated content must be at least 20 characters.';
    }

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setIsSaving(true);
    try {
      if (report) {
        const payload = {
          title: formData.title.trim(),
          author: formData.author.trim() || null,
          tags: formData.tags
            ? formData.tags.split(',').map((tag) => tag.trim()).filter(Boolean)
            : [],
        };

        if (formData.content && formData.content !== report.content) {
          payload.content = formData.content.trim();
        }

        await onSave(payload);
      } else {
        const multipart = new FormData();
        multipart.append('file', file);
        multipart.append('title', formData.title.trim());
        if (formData.author.trim()) multipart.append('author', formData.author.trim());
        if (formData.tags.trim()) multipart.append('tags', formData.tags.trim());
        await onSave(multipart);
      }
    } catch (error) {
      setErrors({ general: error.message || 'Failed to save report.' });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-8"
        onClick={onCancel}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          className="panel max-w-3xl w-full max-h-[90vh] overflow-y-auto"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="panel-header flex items-center justify-between">
            <h2 className="text-xl font-display font-bold text-cockpit-primary">
              {report ? 'Edit Report' : 'Upload Report'}
            </h2>
            <button onClick={onCancel} className="text-cockpit-text-muted hover:text-cockpit-text-primary">
              <X className="w-6 h-6" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="p-6 space-y-5">
            {errors.general && (
              <div className="bg-cockpit-danger/10 border border-cockpit-danger text-cockpit-danger px-4 py-3 rounded">
                {errors.general}
              </div>
            )}

            {!report && (
              <div>
                <label className="label">PDF File *</label>
                <label className="input flex items-center gap-2 cursor-pointer">
                  <Upload className="w-4 h-4 text-cockpit-primary" />
                  <span className="text-sm text-cockpit-text-secondary">
                    {file ? file.name : 'Select PDF report'}
                  </span>
                  <input
                    type="file"
                    accept=".pdf,application/pdf"
                    className="hidden"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                  />
                </label>
                {errors.file && <p className="text-cockpit-danger text-xs mt-1">{errors.file}</p>}
              </div>
            )}

            <div>
              <label className="label">Title *</label>
              <input
                type="text"
                className={`input ${errors.title ? 'border-cockpit-danger' : ''}`}
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              />
              {errors.title && <p className="text-cockpit-danger text-xs mt-1">{errors.title}</p>}
            </div>

            <div>
              <label className="label">Author (Optional)</label>
              <input
                type="text"
                className="input"
                value={formData.author}
                onChange={(e) => setFormData({ ...formData, author: e.target.value })}
              />
            </div>

            <div>
              <label className="label">Tags (Optional)</label>
              <input
                type="text"
                className="input"
                value={formData.tags}
                onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                placeholder="wind-tunnel, cfd, validation"
              />
            </div>

            {report && (
              <div>
                <label className="label">Content (Optional Update)</label>
                <textarea
                  className={`textarea ${errors.content ? 'border-cockpit-danger' : ''}`}
                  rows={8}
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                />
                {errors.content && <p className="text-cockpit-danger text-xs mt-1">{errors.content}</p>}
              </div>
            )}

            <div className="flex items-center gap-3 pt-3 border-t border-cockpit-border">
              <button type="submit" disabled={isSaving} className="btn-primary flex items-center gap-2">
                {report ? <Save className="w-4 h-4" /> : <Upload className="w-4 h-4" />}
                {isSaving ? 'Saving...' : report ? 'Save Changes' : 'Upload Report'}
              </button>
              <button type="button" onClick={onCancel} className="btn-outline">
                Cancel
              </button>
            </div>
          </form>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
