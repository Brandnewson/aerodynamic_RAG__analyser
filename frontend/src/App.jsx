import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import ProtectedRoute from './components/auth/ProtectedRoute';
import { AuthProvider } from './context/AuthContext';
import Dashboard from './pages/Dashboard';
import Documentation from './pages/Documentation';
import HowItWorks from './pages/HowItWorks';
import HealthCheck from './pages/HealthCheck';
import Login from './pages/Login';
import Register from './pages/Register';
import Reports from './pages/Reports';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="reports" element={<Reports />} />
            <Route path="documentation" element={<Documentation />} />
            <Route path="how-it-works" element={<HowItWorks />} />
            <Route path="health" element={<HealthCheck />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
