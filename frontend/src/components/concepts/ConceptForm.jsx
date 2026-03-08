import { useState, useEffect } from 'react';
import { X, Save } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function ConceptForm({ concept, onSave, onCancel }) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    author: '',
    tags: '',
  });

  const [errors, setErrors] = useState({});
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (concept) {
      setFormData({
        title: concept.title || '',
        description: concept.description || '',
        author: concept.author ||'',
        tags: concept.tags ? concept.tags.join(', ') : '',
      });
    }
  }, [concept]);

  const validate = () => {
    const newErrors = {};
    
    if (!formData.title || formData.title.length < 3) {
      newErrors.title = 'Title must be at least 3 characters';
    }
    
    if (!formData.description || formData.description.length < 20) {
      newErrors.description = 'Description must be at least 20 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validate()) return;

    setIsSaving(true);
    
    try {
      const submitData = {
        title: formData.title,
        description: formData.description,
        author: formData.author || null,
        tags: formData.tags 
          ? formData.tags.split(',').map(t => t.trim()).filter(Boolean)
          : [],
      };

      await onSave(submitData);
    } catch (error) {
      console.error('Save failed:', error);
      setErrors({ general: error.message });
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
          transition={{ type: 'spring', damping: 25 }}
          className="panel max-w-3xl w-full max-h-[90vh] overflow-y-auto"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="panel-header flex items-center justify-between sticky top-0 z-10 bg-cockpit-panel">
            <h2 className="text-xl font-display font-bold text-cockpit-primary">
              {concept ? 'Edit Concept' : 'New Concept'}
            </h2>
            <button
              onClick={onCancel}
              className="text-cockpit-text-muted hover:text-cockpit-text-primary transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {errors.general && (
              <div className="bg-cockpit-danger/10 border border-cockpit-danger text-cockpit-danger px-4 py-3 rounded">
                {errors.general}
              </div>
            )}

            {/* Title */}
            <div>
              <label className="label">Title *</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className={`input ${errors.title ? 'border-cockpit-danger' : ''}`}
                placeholder="e.g., Ground effect diffuser with active flow control"
              />
              {errors.title && (
                <p className="text-cockpit-danger text-xs mt-1">{errors.title}</p>
              )}
            </div>

            {/* Description */}
            <div>
              <label className="label">Description *</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className={`textarea ${errors.description ? 'border-cockpit-danger' : ''}`}
                placeholder="Detailed description of the aerodynamic concept, including intended mechanism, target operating conditions, and any known trade-offs..."
                rows={6}
              />
              {errors.description && (
                <p className="text-cockpit-danger text-xs mt-1">{errors.description}</p>
              )}
              <p className="text-xs text-cockpit-text-muted mt-1 font-mono">
                {formData.description.length} characters (minimum 20)
              </p>
            </div>

            {/* Author */}
            <div>
              <label className="label">Author (Optional)</label>
              <input
                type="text"
                value={formData.author}
                onChange={(e) => setFormData({ ...formData, author: e.target.value })}
                className="input"
                placeholder="Your name"
              />
            </div>

            {/* Tags */}
            <div>
              <label className="label">Tags (Optional)</label>
              <input
                type="text"
                value={formData.tags}
                onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                className="input"
                placeholder="downforce, beam-wing, active-aero (comma-separated)"
              />
              <p className="text-xs text-cockpit-text-muted mt-1">
                Comma-separated tags for categorization
              </p>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3 pt-4 border-t border-cockpit-border">
              <button
                type="submit"
                disabled={isSaving}
                className="btn-primary flex items-center gap-2"
              >
                <Save className="w-4 h-4" />
                {isSaving ? 'Saving...' : 'Save Concept'}
              </button>
              <button
                type="button"
                onClick={onCancel}
                className="btn-outline"
              >
                Cancel
              </button>
            </div>
          </form>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
