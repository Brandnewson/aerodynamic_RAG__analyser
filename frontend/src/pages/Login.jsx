import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { LogIn } from 'lucide-react';
import { motion } from 'framer-motion';

import { useAuth } from '../context/AuthContext';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const redirectTo = location.state?.from?.pathname || '/';

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    if (formData.username.trim().length < 3) {
      setError('Username must be at least 3 characters long.');
      return;
    }
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }
    setIsSubmitting(true);
    try {
      await login(formData);
      navigate(redirectTo, { replace: true });
    } catch (submissionError) {
      setError(submissionError.message || 'Login failed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-12">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        className="panel w-full max-w-md"
      >
        <div className="panel-header flex items-center gap-3">
          <LogIn className="w-6 h-6 text-cockpit-primary" />
          <div>
            <h1 className="text-2xl font-display font-bold text-cockpit-primary">Secure Access</h1>
            <p className="text-sm text-cockpit-text-muted font-mono">Login to access AeroInsight</p>
          </div>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {error && (
            <div className="bg-cockpit-danger/10 border border-cockpit-danger text-cockpit-danger px-4 py-3 rounded text-sm">
              {error}
            </div>
          )}
          <div>
            <label className="label">Username</label>
            <input
              type="text"
              className="input"
              value={formData.username}
              onChange={(event) => setFormData({ ...formData, username: event.target.value })}
              minLength={3}
              required
            />
          </div>
          <div>
            <label className="label">Password</label>
            <input
              type="password"
              className="input"
              value={formData.password}
              onChange={(event) => setFormData({ ...formData, password: event.target.value })}
              minLength={8}
              required
            />
          </div>
          <button type="submit" className="btn-primary w-full" disabled={isSubmitting}>
            {isSubmitting ? 'Logging In...' : 'Login'}
          </button>
          <p className="text-sm text-cockpit-text-muted text-center">
            Need an account?{' '}
            <Link to="/register" className="text-cockpit-secondary hover:text-cockpit-primary">
              Register
            </Link>
          </p>
        </form>
      </motion.div>
    </div>
  );
}
