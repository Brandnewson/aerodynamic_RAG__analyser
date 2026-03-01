import { motion } from 'framer-motion';
import { Info, Database, Brain, Search, FileText, Zap, ArrowRight } from 'lucide-react';

export default function HowItWorks() {
  const pipeline = [
    {
      step: 1,
      title: 'Concept Submission',
      icon: FileText,
      description: 'User submits an aerodynamic concept with title, description, and optional metadata.',
      color: 'cockpit-secondary',
    },
    {
      step: 2,
      title: 'Text Embedding',
      icon: Brain,
      description: 'The concept description is embedded using SentenceTransformers (all-MiniLM-L6-v2) into a 384-dimensional vector.',
      color: 'cockpit-primary',
    },
    {
      step: 3,
      title: 'Semantic Retrieval',
      icon: Search,
      description: 'ChromaDB performs cosine similarity search over 31,000+ literature chunks to find the top-k most relevant passages.',
      color: 'cockpit-success',
    },
    {
      step: 4,
      title: 'Prompt Construction',
      icon: Database,
      description: 'Retrieved chunks with full arXiv metadata (title, authors, citations) are formatted into a structured prompt.',
      color: 'cockpit-secondary',
    },
    {
      step: 5,
      title: 'LLM Evaluation',
      icon: Zap,
      description: 'OpenAI GPT-4 analyzes the concept against literature and returns structured JSON (novelty, confidence, mechanisms, tradeoffs).',
      color: 'cockpit-primary',
    },
    {
      step: 6,
      title: 'Response & Attribution',
      icon: FileText,
      description: 'Evaluation is persisted to SQLite and returned with full retrieved_context for citation compliance.',
      color: 'cockpit-success',
    },
  ];

  const techStack = [
    { name: 'FastAPI', purpose: 'REST API framework' },
    { name: 'SQLite', purpose: 'Concept persistence' },
    { name: 'ChromaDB', purpose: 'Vector database (31,652 chunks)' },
    { name: 'SentenceTransformers', purpose: 'Local embeddings (384-dim)' },
    { name: 'OpenAI GPT-4', purpose: 'Structured evaluation' },
    { name: 'arXiv API', purpose: 'Academic paper ingestion (248 papers)' },
    { name: 'React + Tailwind', purpose: 'Frontend UI' },
  ];

  return (
    <div className="min-h-screen">
      <section className="border-b border-cockpit-border bg-cockpit-panel">
        <div className="container mx-auto px-8 py-12">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="flex items-center gap-3 mb-4">
              <Info className="w-8 h-8 text-cockpit-primary" />
              <h1 className="text-4xl font-display font-bold text-cockpit-primary">
                HOW IT WORKS
              </h1>
            </div>
            <p className="text-lg text-cockpit-text-secondary max-w-3xl">
              AeroInsight implements a Retrieval-Augmented Generation (RAG) pipeline 
              to evaluate aerodynamic concepts against 248 academic papers from arXiv.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Pipeline Visualization */}
      <section className="container mx-auto px-8 py-12">
        <div className="max-w-4xl mx-auto space-y-6">
          <h2 className="text-2xl font-display font-bold text-cockpit-text-primary uppercase tracking-wide mb-8">
            RAG Pipeline
          </h2>

          {pipeline.map((item, index) => (
            <motion.div
              key={item.step}
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.15 }}
              className="relative"
            >
              <div className="panel hover:border-cockpit-primary/50 transition-all duration-300">
                <div className="p-6 flex items-start gap-6">
                  {/* Step Number */}
                  <div className={`flex-shrink-0 w-16 h-16 rounded-full bg-${item.color}/20 border-2 border-${item.color} flex items-center justify-center`}>
                    <span className={`text-2xl font-display font-bold text-${item.color}`}>
                      {item.step}
                    </span>
                  </div>

                  {/* Icon */}
                  <div className="flex-shrink-0">
                    <item.icon className={`w-8 h-8 text-${item.color}`} />
                  </div>

                  {/* Content */}
                  <div className="flex-1">
                    <h3 className="text-xl font-display font-bold text-cockpit-text-primary mb-2">
                      {item.title}
                    </h3>
                    <p className="text-sm text-cockpit-text-secondary leading-relaxed">
                      {item.description}
                    </p>
                  </div>
                </div>
              </div>

              {/* Arrow */}
              {index < pipeline.length - 1 && (
                <div className="flex justify-center my-4">
                  <ArrowRight className="w-6 h-6 text-cockpit-primary animate-pulse" />
                </div>
              )}
            </motion.div>
          ))}
        </div>
      </section>

      {/* Tech Stack */}
      <section className="border-t border-cockpit-border bg-cockpit-panel">
        <div className="container mx-auto px-8 py-12">
          <h2 className="text-2xl font-display font-bold text-cockpit-text-primary uppercase tracking-wide mb-8">
            Technology Stack
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-5xl">
            {techStack.map((tech, index) => (
              <motion.div
                key={tech.name}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.8 + index * 0.05 }}
                className="panel p-4 hover:border-cockpit-secondary/50 transition-colors"
              >
                <h3 className="font-display font-bold text-cockpit-primary mb-1">
                  {tech.name}
                </h3>
                <p className="text-sm text-cockpit-text-muted">
                  {tech.purpose}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Architecture Notes */}
      <section className="container mx-auto px-8 py-12">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.2 }}
            className="panel"
          >
            <div className="panel-header">
              <h2 className="font-display font-bold uppercase tracking-wide">
                Hexagonal Architecture
              </h2>
            </div>
            <div className="p-6 space-y-4 text-sm text-cockpit-text-secondary">
              <p>
                The backend follows <strong className="text-cockpit-text-primary">hexagonal (ports and adapters)</strong> architecture:
              </p>
              <ul className="space-y-2 ml-6">
                <li className="flex items-start gap-2">
                  <span className="text-cockpit-primary">→</span>
                  <span><strong className="text-cockpit-primary">Core:</strong> Configuration and settings</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-cockpit-primary">→</span>
                  <span><strong className="text-cockpit-primary">Domain:</strong> ORM models and Pydantic schemas</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-cockpit-primary">→</span>
                  <span><strong className="text-cockpit-primary">Infrastructure:</strong> Database, ChromaDB, and OpenAI adapters</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-cockpit-primary">→</span>
                  <span><strong className="text-cockpit-primary">Services:</strong> Business logic (CRUD, RAG pipeline)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-cockpit-primary">→</span>
                  <span><strong className="text-cockpit-primary">API:</strong> FastAPI routers</span>
                </li>
              </ul>
              <p className="pt-4 border-t border-cockpit-border">
                This separation ensures testability, maintainability, and allows swapping infrastructure 
                components (e.g., PostgreSQL for SQLite, Azure OpenAI for OpenAI) without touching business logic.
              </p>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  );
}
