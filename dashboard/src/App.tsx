import { Routes, Route, Navigate } from 'react-router-dom';
import { isAuthenticated } from './lib/auth';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import AgentsList from './pages/Agents/List';
import AgentDetail from './pages/Agents/Detail';
import Playground from './pages/Playground';
import PlaygroundHistory from './pages/PlaygroundHistory';
import PlaygroundDetail from './pages/PlaygroundDetail';
import Traces from './pages/Traces';
import Logs from './pages/Logs';
import Settings from './pages/Settings';
import './App.css';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  return isAuthenticated() ? <>{children}</> : <Navigate to="/login" replace />;
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/agents" element={<AgentsList />} />
                <Route path="/agents/:agentName" element={<AgentDetail />} />
                <Route path="/playground" element={<Playground />} />
                <Route path="/playground-history" element={<PlaygroundHistory />} />
                <Route path="/playground-history/:promptId" element={<PlaygroundDetail />} />
                <Route path="/traces" element={<Traces />} />
                <Route path="/logs" element={<Logs />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

export default App;
