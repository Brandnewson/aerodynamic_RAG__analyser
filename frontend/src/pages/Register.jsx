import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { UserPlus } from 'lucide-react';
import { motion } from 'framer-motion';

import { useAuth } from '../context/AuthContext';

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ username: '', password: '', confirmPassword: '' });
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const hasNumber = /\d/.test(formData.password);
  const hasSpecialCharacter = /[^A-Za-z0-9\s]/.test(formData.password);

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
    if (!hasNumber) {
      setError('Password must include at least one number.');
      return;
    }
    if (!hasSpecialCharacter) {
      setError('Password must include at least one special character.');
      return;
    }
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setIsSubmitting(true);
    try {
      await register({ username: formData.username, password: formData.password });
      navigate('/', { replace: true });
    } catch (submissionError) {
      setError(submissionError.message || 'Registration failed.');
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
          <UserPlus className="w-6 h-6 text-cockpit-secondary" />
          <div>
            <h1 className="text-2xl font-display font-bold text-cockpit-secondary">Create Account</h1>
            <p className="text-sm text-cockpit-text-muted font-mono">Register for protected access</p>
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
            <p className="text-xs text-cockpit-text-muted mt-2 font-mono">
              Minimum 8 characters, including one number and one special character.
            </p>
          </div>
          <div>
            <label className="label">Confirm Password</label>
            <input
              type="password"
              className="input"
              value={formData.confirmPassword}
              onChange={(event) => setFormData({ ...formData, confirmPassword: event.target.value })}
              minLength={8}
              required
            />
          </div>
          <button type="submit" className="btn-secondary w-full" disabled={isSubmitting}>
            {isSubmitting ? 'Creating Account...' : 'Register'}
          </button>
          <p className="text-sm text-cockpit-text-muted text-center">
            Already registered?{' '}
            <Link to="/login" className="text-cockpit-primary hover:text-cockpit-secondary">
              Login
            </Link>
          </p>
        </form>
      </motion.div>
    </div>
  );
}
