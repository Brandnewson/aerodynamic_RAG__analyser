import { NavLink } from 'react-router-dom';
import { 
  Gauge, 
  FolderOpen,
  FileText, 
  Info, 
  Activity,
  ChevronRight,
  LogOut,
  ShieldCheck,
} from 'lucide-react';
import { motion } from 'framer-motion';

import { useAuth } from '../../context/AuthContext';

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navItems = [
    { 
      path: '/', 
      label: 'Mission Control', 
      icon: Gauge,
      description: 'Main Dashboard'
    },
    {
      path: '/reports',
      label: 'Reports',
      icon: FolderOpen,
      description: 'Vector Report CRUD'
    },
    { 
      path: '/documentation', 
      label: 'Documentation', 
      icon: FileText,
      description: 'API Reference'
    },
    { 
      path: '/how-it-works', 
      label: 'How It Works', 
      icon: Info,
      description: 'System Overview'
    },
    { 
      path: '/health', 
      label: 'System Status', 
      icon: Activity,
      description: 'Health Checks'
    },
  ];

  return (
    <motion.aside
      initial={{ x: -300, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className="w-72 bg-cockpit-panel border-r border-cockpit-border flex flex-col h-screen sticky top-0"
    >
      {/* Header */}
      <div className="p-6 border-b border-cockpit-border">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.4 }}
        >
          <h1 className="text-2xl font-display font-bold text-cockpit-primary text-glow">
            AEROINSIGHT
          </h1>
          <p className="text-xs text-cockpit-text-muted mt-1 font-mono uppercase tracking-wider">
            Aerodynamic RAG System
          </p>
        </motion.div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item, index) => (
          <motion.div
            key={item.path}
            initial={{ x: -50, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.3 + index * 0.1, duration: 0.3 }}
          >
            <NavLink
              to={item.path}
              className={({ isActive }) =>
                `group flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                  isActive
                    ? 'bg-cockpit-primary/20 text-cockpit-primary border border-cockpit-primary/50'
                    : 'text-cockpit-text-secondary hover:bg-cockpit-highlight hover:text-cockpit-text-primary'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon 
                    className={`w-5 h-5 transition-transform duration-200 ${
                      isActive ? 'scale-110' : 'group-hover:scale-110'
                    }`} 
                  />
                  <div className="flex-1">
                    <div className="font-display font-semibold text-sm uppercase tracking-wide">
                      {item.label}
                    </div>
                    <div className="text-xs text-cockpit-text-muted">
                      {item.description}
                    </div>
                  </div>
                  <ChevronRight 
                    className={`w-4 h-4 transition-all duration-200 ${
                      isActive ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0'
                    }`}
                  />
                </>
              )}
            </NavLink>
          </motion.div>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-cockpit-border">
        <div className="mb-4 rounded border border-cockpit-secondary/30 bg-cockpit-bg/70 p-3">
          <div className="flex items-center gap-2 text-cockpit-secondary">
            <ShieldCheck className="w-4 h-4" />
            <span className="text-xs font-mono uppercase tracking-wider">Authenticated</span>
          </div>
          <div className="mt-2 text-sm text-cockpit-text-primary font-mono">{user?.username || 'Unknown User'}</div>
          <button onClick={logout} className="btn-outline mt-3 w-full flex items-center justify-center gap-2">
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>
        <div className="text-xs text-cockpit-text-muted font-mono">
          <div className="flex justify-between mb-1">
            <span>System Status</span>
            <span className="text-cockpit-success">● OPERATIONAL</span>
          </div>
          <div className="flex justify-between">
            <span>Version</span>
            <span>v0.1.0</span>
          </div>
        </div>
      </div>
    </motion.aside>
  );
}
