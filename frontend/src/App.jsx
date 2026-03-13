import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import Documentation from './pages/Documentation';
import HowItWorks from './pages/HowItWorks';
import HealthCheck from './pages/HealthCheck';
import Reports from './pages/Reports';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="reports" element={<Reports />} />
          <Route path="documentation" element={<Documentation />} />
          <Route path="how-it-works" element={<HowItWorks />} />
          <Route path="health" element={<HealthCheck />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
