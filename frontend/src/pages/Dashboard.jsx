import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Plus, Filter, RefreshCw, Zap } from 'lucide-react';
import { conceptsApi, evaluationsApi } from '../services/api';
import ConceptCard from '../components/concepts/ConceptCard';
import ConceptForm from '../components/concepts/ConceptForm';
import EvaluationResult from '../components/evaluations/EvaluationResult';

export default function Dashboard() {
  const [concepts, setConcepts] = useState([]);
  const [filteredConcepts, setFilteredConcepts] = useState([]);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [isLoading, setIsLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingConcept, setEditingConcept] = useState(null);
  
  // Evaluation state
  const [selectedConcept, setSelectedConcept] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [isEvaluating, setIsEvaluating] = useState(false);

  useEffect(() => {
    loadConcepts();
  }, []);

  useEffect(() => {
    if (statusFilter === 'ALL') {
      setFilteredConcepts(concepts);
    } else {
      setFilteredConcepts(concepts.filter(c => c.status === statusFilter));
    }
  }, [concepts, statusFilter]);

  const loadConcepts = async () => {
    setIsLoading(true);
    try {
      const response = await conceptsApi.list({ pageSize: 100 });
      setConcepts(response.items || []);
    } catch (error) {
      console.error('Failed to load concepts:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingConcept(null);
    setShowForm(true);
  };

  const handleEdit = (concept) => {
    setEditingConcept(concept);
    setShowForm(true);
  };

  const handleSave = async (data) => {
    try {
      if (editingConcept) {
        await conceptsApi.update(editingConcept.id, data);
      } else {
        await conceptsApi.create(data);
      }
      setShowForm(false);
      setEditingConcept(null);
      loadConcepts();
    } catch (error) {
      throw new Error(error.message || 'Failed to save concept');
    }
  };

  const handleDelete = async (concept) => {
    if (!window.confirm(`Delete "${concept.title}"?`)) return;
    
    try {
      await conceptsApi.delete(concept.id);
      loadConcepts();
      if (selectedConcept?.id === concept.id) {
        setSelectedConcept(null);
        setEvaluation(null);
      }
    } catch (error) {
      alert('Failed to delete concept');
    }
  };

  const handleEvaluate = async (concept) => {
    setSelectedConcept(concept);
    setEvaluation(null);
    setIsEvaluating(true);

    try {
      const result = await evaluationsApi.evaluate(concept.id);
      setEvaluation(result);
      loadConcepts(); // Refresh to update status
      
      // Scroll to evaluation section
      setTimeout(() => {
        document.getElementById('evaluation-section')?.scrollIntoView({ 
          behavior: 'smooth',
          block: 'start'
        });
      }, 100);
    } catch (error) {
      alert(`Evaluation failed: ${error.message}`);
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleViewEvaluation = async (concept) => {
    setSelectedConcept(concept);
    setEvaluation(null);
    setIsEvaluating(true);

    try {
      const result = await evaluationsApi.get(concept.id);
      setEvaluation(result);
      
      // Scroll to evaluation section
      setTimeout(() => {
        document.getElementById('evaluation-section')?.scrollIntoView({ 
          behavior: 'smooth',
          block: 'start'
        });
      }, 100);
    } catch (error) {
      alert(`Failed to load evaluation: ${error.message}`);
    } finally {
      setIsEvaluating(false);
    }
  };

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="border-b border-cockpit-border bg-gradient-to-b from-cockpit-panel to-cockpit-bg">
        <div className="container mx-auto px-8 py-12">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-4xl"
          >
            <div className="flex items-center gap-3 mb-4">
              <Zap className="w-8 h-8 text-cockpit-primary" />
              <h1 className="text-4xl font-display font-bold text-cockpit-primary text-glow">
                MISSION CONTROL
              </h1>
            </div>
            <p className="text-lg text-cockpit-text-secondary leading-relaxed">
              AI-augmented aerodynamic concept evaluation platform. Submit concepts, 
              trigger RAG-powered analysis, and explore retrieved academic literature.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Concepts Section */}
      <section className="border-b border-cockpit-border">
        <div className="container mx-auto px-8 py-12">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl font-display font-bold text-cockpit-text-primary uppercase tracking-wide mb-2">
                Concept Database
              </h2>
              <p className="text-sm text-cockpit-text-muted font-mono">
                {filteredConcepts.length} concepts {statusFilter !== 'ALL' && `(${statusFilter})`}
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={loadConcepts}
                className="btn-outline flex items-center gap-2"
                disabled={isLoading}
              >
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
              
              <button
                onClick={handleCreate}
                className="btn-primary flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                New Concept
              </button>
            </div>
          </div>

          {/* Filter Bar */}
          <div className="flex items-center gap-2 mb-6">
            <Filter className="w-4 h-4 text-cockpit-text-muted" />
            <span className="text-sm text-cockpit-text-muted font-display uppercase">
              Filter:
            </span>
            {['ALL', 'SUBMITTED', 'ANALYSED'].map(status => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={`px-3 py-1 rounded text-xs font-display font-bold uppercase transition-all ${
                  statusFilter === status
                    ? 'bg-cockpit-primary text-black'
                    : 'bg-cockpit-highlight text-cockpit-text-secondary hover:bg-cockpit-border'
                }`}
              >
                {status}
              </button>
            ))}
          </div>

          {/* Concepts Grid */}
          {isLoading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-cockpit-primary border-t-transparent"></div>
            </div>
          ) : filteredConcepts.length === 0 ? (
            <div className="panel">
              <div className="p-12 text-center text-cockpit-text-muted">
                No concepts found. Create your first concept to get started.
              </div>
            </div>
          ) : (
            <div className="grid gap-6">
              {filteredConcepts.map(concept => (
                <ConceptCard
                  key={concept.id}
                  concept={concept}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                  onEvaluate={handleEvaluate}
                  onViewEvaluation={handleViewEvaluation}
                />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Evaluation Section */}
      <section id="evaluation-section" className="bg-cockpit-bg">
        <div className="container mx-auto px-8 py-12">
          <div className="mb-8">
            <h2 className="text-2xl font-display font-bold text-cockpit-text-primary uppercase tracking-wide mb-2">
              RAG Evaluation Analysis
            </h2>
            {selectedConcept ? (
              <p className="text-sm text-cockpit-text-secondary">
                Analyzing: <span className="text-cockpit-primary font-semibold">{selectedConcept.title}</span>
              </p>
            ) : (
              <p className="text-sm text-cockpit-text-muted font-mono">
                Select a concept and click "Evaluate" to begin
              </p>
            )}
          </div>

          <EvaluationResult 
            evaluation={evaluation} 
            isLoading={isEvaluating}
          />
        </div>
      </section>

      {/* Form Modal */}
      {showForm && (
        <ConceptForm
          concept={editingConcept}
          onSave={handleSave}
          onCancel={() => {
            setShowForm(false);
            setEditingConcept(null);
          }}
        />
      )}
    </div>
  );
}
